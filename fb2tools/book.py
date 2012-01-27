# coding=utf-8
from lxml import etree
import hashlib
import re
from fb2tools.xpath import TITLE_INFO, SRC_TITLE_INFO, first_or_none
import os
from zipfile import ZipFile, ZIP_DEFLATED
from . import NotAFBZException, FB2_NSMAP, X_REF
from fb2tools import fb2tag
from xpath import ELEMENTS_WITH_ID, ELEMENTS_WITH_REF

BOOK_TITLE = etree.XPath('//f:description/f:title-info/f:book-title', namespaces=FB2_NSMAP)
BODY = etree.XPath('//f:FictionBook/f:body', namespaces=FB2_NSMAP)

EPIGRAPH = etree.XPath('//f:FictionBook/f:body[0]/f:epigraph', namespaces=FB2_NSMAP)
COVER = etree.XPath('//f:description/f:title-info/f:coverpage/f:image[0]', namespaces=FB2_NSMAP)
ANNOTATION = etree.XPath('//f:description/f:title-info/f:annotation', namespaces=FB2_NSMAP)

BINARY = etree.XPath('//f:FictionBook/f:binary', namespaces=FB2_NSMAP)

class Book(object):
    FB2_SCHEMA = os.path.join(os.path.dirname(__file__), 'schema', 'FictionBook2.1.xsd')
    SCHEMA = etree.XMLSchema(file=FB2_SCHEMA)

    def __init__(self, path, tree, saveMethod=None, strict=False):
        self._path = path
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
        inzip = False
        if path.endswith('.fb2.zip') or path.endswith('.fbz'):
            fo = cls.openZip(fo)
            inzip = True

        tree = etree.parse(fo)
        fo.close()

        return Book(path, tree, inzip, strict)

    @classmethod
    def fromParsed(cls, tree, path, strict=False):
        return Book(path, tree, strict=strict)

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

    def getTitle(self):
        return BOOK_TITLE(self._tree)[0].text

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

    def saveAs(self, filename, zip=False, zip_internal=None):
        xml = etree.tostring(self._tree, xml_declaration=True, pretty_print=True, encoding='utf-8')

        if not filename.endswith('.fb2'):
            filename += '.fb2'

        if zip:
            if zip_internal is None:
                #noinspection PyRedeclaration
                zip_internal = 'book.fb2'
            z = ZipFile(filename + '.zip', 'w', ZIP_DEFLATED)
            z.writestr(zip_internal, xml)
            z.close()
        else:
            obook = open(filename, 'w')
            obook.write(xml)
            obook.close()
