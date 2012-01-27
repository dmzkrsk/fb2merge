# coding=utf-8
from lxml import etree
from . import FB2_NSMAP

TITLE_INFO = etree.XPath('//f:description/f:title-info', namespaces=FB2_NSMAP)
SRC_TITLE_INFO = etree.XPath('//f:description/f:src-title-info', namespaces=FB2_NSMAP)
SRC_URL = etree.XPath('//f:description/f:document-info/f:src-url', namespaces=FB2_NSMAP)
SRC_OCR = etree.XPath('//f:description/f:document-info/f:src-ocr', namespaces=FB2_NSMAP)

ELEMENTS_WITH_ID = etree.XPath('//*[@id]')
ELEMENTS_WITH_REF = etree.XPath('//*[@x:href and starts-with(@x:href, "#")]', namespaces=FB2_NSMAP)

def first_or_none(selector, tree):
    l = selector(tree)

    if not l:
        return None
    return l[0]
