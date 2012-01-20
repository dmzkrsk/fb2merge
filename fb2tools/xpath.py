# coding=utf-8
from lxml import etree
from . import FB2_NSMAP

TITLE_INFO = etree.XPath('//f:description/f:title-info', namespaces=FB2_NSMAP)
SRC_TITLE_INFO = etree.XPath('//f:description/f:src-title-info', namespaces=FB2_NSMAP)
SRC_URL = etree.XPath('//f:description/f:document-info/f:src-url', namespaces=FB2_NSMAP)
SRC_OCR = etree.XPath('//f:description/f:document-info/f:src-ocr', namespaces=FB2_NSMAP)

EPIGRAPH = etree.XPath('//f:FictionBook/f:body[0]/f:epigraph', namespaces=FB2_NSMAP)
COVER = etree.XPath('//f:description/f:title-info/f:coverpage/f:image[0]', namespaces=FB2_NSMAP)
ANNOTATION = etree.XPath('//f:description/f:title-info/f:annotation', namespaces=FB2_NSMAP)

BODY = etree.XPath('//f:FictionBook/f:body', namespaces=FB2_NSMAP)
BINARY = etree.XPath('//f:FictionBook/f:binary', namespaces=FB2_NSMAP)

def first_or_none(selector, tree):
    l = selector(tree)

    if not l:
        return None
    return l[0]
