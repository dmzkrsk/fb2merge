# coding=utf-8
from itertools import dropwhile
from lxml import etree
import hashlib
from operator import attrgetter
import re
from fb2tools.xpath import TITLE_INFO, SRC_TITLE_INFO, first_or_none
import os
from zipfile import ZipFile
from . import NotAFBZException, FB2_NSMAP, X_REF
from fb2tools import fb2tag
from xpath import ELEMENTS_WITH_ID, ELEMENTS_WITH_REF
from xml import build_element as _e
from save import SaveXml, SaveZip

BOOK_TITLE = etree.XPath('//f:description/f:title-info/f:book-title', namespaces=FB2_NSMAP)
ORIGINAL_TITLE = etree.XPath('//f:description/f:src-title-info/f:book-title', namespaces=FB2_NSMAP)
BODY = etree.XPath('//f:FictionBook/f:body', namespaces=FB2_NSMAP)

AUTHORS = etree.XPath('//f:description/f:title-info/f:author', namespaces=FB2_NSMAP)

EPIGRAPH = etree.XPath('//f:FictionBook/f:body[0]/f:epigraph', namespaces=FB2_NSMAP)
COVER = etree.XPath('//f:description/f:title-info/f:coverpage/f:image[0]', namespaces=FB2_NSMAP)
ANNOTATION = etree.XPath('//f:description/f:title-info/f:annotation', namespaces=FB2_NSMAP)

BINARY = etree.XPath('//f:FictionBook/f:binary', namespaces=FB2_NSMAP)

_DS_INFO = etree.XPath('//f:description/*[contains(local-name(), "title-info")]', namespaces=FB2_NSMAP)
_TAGS_BEFORE_DATE = map(fb2tag, ['genre', 'author', 'book-title', 'annotation', 'keywords'])

class Book(object):
    FB2_SCHEMA = os.path.join(os.path.dirname(__file__), 'schema', 'FictionBook2.1.xsd')
    SCHEMA = etree.XMLSchema(file=FB2_SCHEMA)

    def __init__(self, tree, strict=False, saveMethod=None):
        self._tree = tree
        self._strict = strict
        self._saveMethod = saveMethod

        if self._strict:
            self.SCHEMA.assertValid(self._tree)
            self._valid = True
        else:
            self._valid = self.SCHEMA.validate(self._tree)

    @classmethod
    def fromFile(cls, path, strict=False):
        fo = open(path, 'r')
        saveMethod = SaveXml(path)
        if path.endswith('.fb2.zip') or path.endswith('.fbz'):
            fo = cls.openZip(fo)
            saveMethod = SaveZip(path, fo.name)

        tree = etree.parse(fo)
        fo.close()

        return Book(tree, strict, saveMethod)

    @classmethod
    def fromParsed(cls, tree, strict=False):
        return Book(tree, strict)

    @classmethod
    def openZip(cls, fo):
        z = ZipFile(fo)
        zfiles = z.infolist()
        if len(zfiles) == 1:
            return z.open(zfiles[0].filename)

        raise NotAFBZException()

    @classmethod
    def validate_ext(cls, tree):
        return cls.SCHEMA.validate(tree)

    def validate(self):
        return self.SCHEMA.validate(self._tree)

    @classmethod
    def rebuild_id(cls, oldID, globalID):
        m = hashlib.md5()
        m.update(globalID)
        m.update(oldID)

        return 'id-'+m.hexdigest()

    def rebuildID(self, bookID, refs):
        for e in ELEMENTS_WITH_ID(self._tree):
            e.attrib['id'] = self.rebuild_id(e.attrib['id'], str(bookID))

        for e in ELEMENTS_WITH_REF(self._tree):
            newRef = self.rebuild_id(e.attrib[X_REF][1:], str(bookID))
            e.attrib[X_REF] = '#' + newRef
            refs.append(newRef)

    def xpath(self, xpath):
        return xpath(self._tree)

    def setYearAggressive(self, year):
        year_str = str(year)

        tree_changed = False
        for info in _DS_INFO(self._tree):
            dt = dropwhile(lambda x: x.tag in _TAGS_BEFORE_DATE, info).next()
            if dt.tag == fb2tag('date'):
                if dt.text == year_str and dt.attrib.get('value') is None:
                    continue

                if 'value' in dt.attrib:
                    del dt.attrib['value']

                dt.text = year_str
                tree_changed = True
            else:
                dt.addprevious(_e('date', year_str))
                tree_changed = True

        return tree_changed

    def getYearAggressive(self):
        dates = []
        for ti in [TITLE_INFO, SRC_TITLE_INFO]:
            ti_item = ti(self._tree)
            if not ti_item:
                continue

            dates.extend(
                filter(None, (x.attrib.get('value', x.text) for x in ti_item[0] if x.tag == fb2tag('date')))
            )

        xy = lambda x: max(map(int, re.split('\D+', x)))
        dv = filter(None, map(xy, dates))
        return min(dv) if dv else None

    def getTitle(self, original=False):
        return first_or_none(ORIGINAL_TITLE if original else BOOK_TITLE, self._tree, attrgetter('text'))

    def getAuthors(self):
        return AUTHORS(self._tree)

    def getBodies(self):
        return BODY(self._tree)

    def getAnnotation(self):
        return first_or_none(ANNOTATION, self._tree)

    def getEpigraphs(self):
        return EPIGRAPH(self._tree)

    def getCover(self):
        return first_or_none(COVER, self._tree)

    def getBinaries(self):
        return BINARY(self._tree)

    def save(self):
        if self._strict or self._valid:
            assert self.validate()

        if self._saveMethod is None:
            raise RuntimeError("Cannot save book")

        self._saveMethod.save(self.dump())

    def saveAs(self, filename, zip=False, zip_internal=None):
        if not filename.endswith('.fb2'):
            filename += '.fb2'

        if zip:
            if zip_internal is None:
                #noinspection PyRedeclaration
                zip_internal = 'book.fb2'
            s = SaveZip(filename + '.zip', zip_internal)
        else:
            s = SaveXml(filename)

        s.save(self.dump())

    def dump(self):
        return etree.tostring(self._tree, xml_declaration=True, pretty_print=True, encoding='utf-8')

