# coding=utf-8
from bisect import bisect_right
from collections import namedtuple
import getpass
from itertools import chain
from lxml import etree
import hashlib
from datetime import datetime
import uuid
import os
import time
from zipfile import ZipFile, ZIP_DEFLATED
from . import FB2_NSMAP, X_REF, LIB_NAME, fb2tag, NotAFBZException
from .fb2 import extract_year
from .stat import TitleInfo, SrcURL, SrcOCR
from .xpath import TITLE_INFO, SRC_TITLE_INFO, SRC_URL, SRC_OCR
from .xml import build_element as _e

ELEMENTS_WITH_ID = etree.XPath('//*[@id]')
ELEMENTS_WITH_REF = etree.XPath('//*[@x:href and starts-with(@x:href, "#")]', namespaces=FB2_NSMAP)

BOOK_TITLE = etree.XPath('//f:description/f:title-info/f:book-title', namespaces=FB2_NSMAP)

def rebuild_id(oldID, globalID):
    m = hashlib.md5()
    m.update(globalID)
    m.update(oldID)

    return 'id-'+m.hexdigest()

class BookInfo(object):
    Key = namedtuple('BookInfo', 'year,sequence,title')

    def __init__(self, refs, year, sequence, title):
        self.key = BookInfo.Key(year, sequence, title)
        self._refs = dict(zip(refs, refs))

    def referes(self, id):
        return id in self._refs

class BookStat(object):
    def __init__(self):
        self.titleInfo = TitleInfo(TITLE_INFO)
        self.srcTitleInfo = TitleInfo(SRC_TITLE_INFO, False)
        self.srcUrl = SrcURL(SRC_URL, False)
        self.srcOcr = SrcOCR(SRC_OCR, False)

    def process(self, tree, bookID):
        self.titleInfo.add(tree)
        self.srcTitleInfo.add(tree)
        self.srcUrl.add(tree)
        self.srcOcr.add(tree)

        refs = []
        self.fixID(tree, bookID, refs)

        title = BOOK_TITLE(tree)[0].text
        sequence = None
        year = extract_year(tree) or float('inf')
        return BookInfo(refs, year, sequence, title)

    @classmethod
    def fixID(cls, tree, bookID, refs):
        for e in ELEMENTS_WITH_ID(tree):
            e.attrib['id'] = rebuild_id(e.attrib['id'], str(bookID))

        for e in ELEMENTS_WITH_REF(tree):
            newRef = rebuild_id(e.attrib[X_REF][1:], str(bookID))
            e.attrib[X_REF] = '#' + newRef
            refs.append(newRef)

class Book(object):
    FB2_SCHEMA = os.path.join(os.path.dirname(__file__), 'schema', 'FictionBook2.1.xsd')
    SCHEMA = etree.XMLSchema(file=FB2_SCHEMA)

    def __init__(self, title):
        self._r = _e("FictionBook", None)
        self._description = _e('description', None)
        self._r.append(self._description)

        self._main = _e('body', None,
            _e('title', None, _e('p', title)),
        )

        self._r.append(self._main)
        self._notes = []

        self._keys = []

        self._title = title

    def insertBook(self, key, section, notes):
        insertPos = bisect_right(self._keys, key)
        self._keys.insert(insertPos, key)
        self._main.insert(insertPos + 1, section)
        self._notes.insert(insertPos, notes)

    def addBinary(self, binary):
        self._r.append(binary)

    def _addTitleInfo(self, titleInfo):
        tiData = titleInfo.write(bookTitle=self._title)
        self._description.insert(0, _e('title-info', None, *tiData))

    def _addDocumentInfo(self, srcUrl, srcOcr):
        td = datetime.today()
        bookVersion = '%d' % time.mktime(td.timetuple())
        bookId = str(uuid.uuid4())

        diInfo = [
                     _e('author', None, _e('nickname', getpass.getuser())),
                     _e('program-used', LIB_NAME),
                     _e('date', td.strftime("%d %B, %Y"), value=td.strftime("%Y-%m-%d")),
                     ] + list(srcUrl.write()) + list(srcOcr.write()) + [
            _e('id', bookId),
            _e('version', bookVersion),
            ]

        self._description.append(_e('document-info', None, *diInfo))

    def save(self, o):
        obook = open(o + '.fb2', 'w')
        print >>obook, etree.tostring(self._r, xml_declaration=True, pretty_print=True, encoding='utf-8')
        obook.close()

    def savez(self, o):
        z = ZipFile(o + '.fb2.zip', 'w', ZIP_DEFLATED)
        xml = etree.tostring(self._r, xml_declaration=True, pretty_print=True, encoding='utf-8')
        z.writestr('book.fb2', xml)
        z.close()

    def validate(self):
        return self.SCHEMA.assertValid(self._r)

    def finish(self, stat):
        """
        :type stat: BookStat
        """
        self._addTitleInfo(stat.titleInfo)
        self._addDocumentInfo(stat.srcUrl, stat.srcOcr)

        # Clean references

        notesflat = []
        noteIDs = []
        for pos, note in enumerate(chain(*self._notes)):
            noteIDs.append(note.attrib['id'])
            if note[0].tag == fb2tag('title'):
                note.replace(note[0], _e('title', None, _e('p', str(pos + 1))))
            notesflat.append(note)

        notenum = 1
        allRef = [e.attrib['id'] for e in ELEMENTS_WITH_ID(self._r)]

        referred = []
        for noteref in ELEMENTS_WITH_REF(self._main):
            ref = noteref.attrib[X_REF][1:]
            if ref in noteIDs:
                noteref.text = '[%d]' % notenum
                notenum += 1
                referred.append(ref)
            elif ref in allRef:
                referred.append(ref)
            else:
                prev = noteref.getprevious()
                parent = noteref.getparent()
                # http://hustoknow.blogspot.com/2011/09/lxml-bug.html
                if not prev:
                    parent.text = (parent.text or '') + noteref.tail
                else:
                    prev.tail = (prev.tail or '') + noteref.tail

                parent.remove(noteref)

        for e in ELEMENTS_WITH_ID(self._main):
            if e.attrib['id'] not in referred:
                if e.tag == fb2tag('p'):
                    del e.attrib['id']
                else:
                    assert False, e.tag

        if notesflat:
            self._notes = _e('body', None, name="notes", *notesflat)
            self._r.insert(2, self._notes)

    @classmethod
    def validate_ext(cls, tree):
        return cls.SCHEMA.validate(tree)

    @classmethod
    def openZip(cls, fo):
        z = ZipFile(fo)
        zfiles = z.infolist()
        if len(zfiles) == 1:
            return z.open(zfiles[0].filename)

        raise NotAFBZException()
