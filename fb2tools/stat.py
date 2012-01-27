# coding=utf-8
import hashlib
from . import fb2tag
from operator import itemgetter
from .xml import build_element as _e

def xml_text_hash(tag):
    m = hashlib.md5()
    for atag in sorted(tag, key=lambda x:x.tag):
        m.update(atag.text.encode('utf-8') if atag.text else '|')

    return m.hexdigest()

class XPathInfo(object):
    def __init__(self, xpath, required):
        self._xpath = xpath
        self._required = required
        self._c = 0

    def __nonzero__(self):
        return bool(self._c)

    def add(self, book):
        """
        :type book: book.Book
        """
        i = book.xpath(self._xpath)
        if not len(i):
            if self._required:
                raise ValueError('No title info data found')
            else:
                return

        self._c += 1
        self._add(i)

    def _add(self, i):
        for e in i[0]:
            self._process(e)

    def _process(self, e):
        raise NotImplementedError()

    def write(self, **meta):
        if not self._c:
            return []

        return self._write(**meta)

    def _write(self, **meta):
        """
        :rtype: list
        """
        raise NotImplementedError()

class SrcURL(XPathInfo):
    def __init__(self, xpath, required=True):
        super(SrcURL, self).__init__(xpath, required)

        self.urls = {}

    def _add(self, i):
        for e in i:
            self._process(e)

    def _process(self, e):
        if e.text:
            self.urls[e.text] = e

    def _write(self, **meta):
        return (x for x in self.urls.itervalues())

class SrcOCR(SrcURL):
    def _write(self, **meta):
        tx = '. '.join(self.urls.keys())
        yield _e(self.urls.values()[0].tag, tx)

class TitleInfo(XPathInfo):
    def __init__(self, xpath, required=True):
        super(TitleInfo, self).__init__(xpath, required)

        self.genres = {}
        self.authors = {}
        self.translators = {}
        self.langs = {}
        self.srclangs = {}
        self.sequences = []

    def _process(self, e):
        if e.tag == fb2tag('genre'):
            g = e.text.strip()
            self.genres[g] = max(self.genres.get(g, 100), int(e.attrib.get('match', 100)))
        elif e.tag == fb2tag('author'):
            self.authors[xml_text_hash(e)] = e
        elif e.tag == fb2tag('translator'):
            self.translators[xml_text_hash(e)] = e
        elif e.tag == fb2tag('lang'):
            self.langs[e.text] = self.langs.get(e.text, 0) + 1
        elif e.tag == fb2tag('src-lang'):
            self.srclangs[e.text] = self.srclangs.get(e.text, 0) + 1
        elif e.tag == fb2tag('sequence'):
            self.sequences.append(e)

    def _write(self, **meta):
        for genre, match in self.genres.iteritems():
            attr = {'match': str(match)} if match < 100 else {}
            yield _e('genre', genre, **attr)

        for a in self.authors.values():
            yield a

        yield _e('book-title', meta['bookTitle'])

        if self.langs:
            lang = sorted(self.langs.iteritems(), key=itemgetter(1))[0][0]
            yield _e('lang', lang)

        if self.srclangs:
            lang = sorted(self.srclangs.iteritems(), key=itemgetter(1))[0][0]
            yield _e('src-lang', lang)

        for a in self.translators.itervalues():
            yield a

        for a in self.sequences:
            yield a

