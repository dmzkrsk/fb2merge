# coding=utf-8
LIB_NAME = 'fb2merge'

FB2_NSMAP = {
    'f': 'http://www.gribuser.ru/xml/fictionbook/2.0',
    'x': 'http://www.w3.org/1999/xlink',
}

FB2_NSMAP_OUT = {
    None: FB2_NSMAP['f'],
    'xlink': FB2_NSMAP['x'],
}

X_REF = '{%s}href' % FB2_NSMAP['x']

class ArgumentsException(Exception):
    pass

class NotAFBZException(Exception):
    pass

def fb2tag(tag):
    return '{%s}%s' % (FB2_NSMAP['f'], tag)
