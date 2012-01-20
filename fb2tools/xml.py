# coding=utf-8
from lxml import etree
from . import FB2_NSMAP_OUT, fb2tag

def build_element(tag, content, *children, **attrib):
    if tag[0] != '{':
        #noinspection PyRedeclaration
        tag = fb2tag(tag)

    e = etree.Element(tag, attrib, nsmap=FB2_NSMAP_OUT)
    if content is not None:
        e.text = content

    for sub in children:
        e.append(sub)

    return e
