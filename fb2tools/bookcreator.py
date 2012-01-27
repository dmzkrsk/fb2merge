# coding=utf-8
from bisect import bisect_right
from collections import namedtuple
import getpass
from itertools import chain
from datetime import datetime
import uuid
import time
from . import X_REF, LIB_NAME, fb2tag
from .stat import TitleInfo, SrcURL, SrcOCR
from .xpath import *
from .xml import build_element as _e
from .book import Book

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

    def process(self, book, bookID):
        self.titleInfo.add(book)
        self.srcTitleInfo.add(book)
        self.srcUrl.add(book)
        self.srcOcr.add(book)

        refs = []
        book.rebuildID(bookID, refs)

        title = book.getTitle()
        sequence = None
        year = book.getYearAggressive() or float('inf')
        return BookInfo(refs, year, sequence, title)

class BookCreator(object):
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

        return Book.fromParsed(self._r, True)
