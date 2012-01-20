# coding=utf-8
from . import fb2tag
from itertools import chain
import re
from .fb2 import fb2title
from .xml import build_element as _e

BAD_TITLE = re.compile('^[* ]+$')

class Section(object):
    def __init__(self, section):
        self.images = []
        self.titles = []
        self.epigraphs = []
        self.annotations = []

        pos = 0

        for pos, bc in enumerate(section):
            if bc.tag == fb2tag('image'):
                self.images.append(bc)
            elif bc.tag == fb2tag('title') and len(bc):
                self.titles.append(bc)
            elif bc.tag == fb2tag('epigraph') and len(bc):
                self.epigraphs.append(bc)
            elif bc.tag == fb2tag('annotation') and len(bc):
                self.annotations.append(bc)
            else:
                break

        self.content = section[pos:]

        assert 0 <= len(self.titles) <= 1

        if len(self.titles) == 1:
            ntitle = fb2title(self.titles[0])
            if not ntitle or BAD_TITLE.match(ntitle):
                self.titles = []
            else:
                self.titles = [_e('title', None, _e('p', ntitle))]

    def simple(self):
        return len(self.content) == 1 and self.content[0].tag == fb2tag('section')

    def rebuild_section(self, **meta):
        if not self.simple():
            return self._rebuild(self, **meta)

        # merge body
        # Ignore body.title
        fs = Section(self.content[0])
        fs.epigraphs = self.epigraphs + fs.epigraphs
        return self._rebuild(fs, **meta)

    @classmethod
    def _rebuild(cls, section_parsed, **meta):
        data = []

        assert meta['title']
        # Ignore sp.titles
        data.append(_e('title', None, _e('p', meta['title'])))

        data.extend(chain(meta['epigraphs'], section_parsed.epigraphs)) # 0..n

        # Ignore sp.images
        if meta['cover'] is not None:
            data.append(meta['cover']) # 0..1

        if meta['annotation'] is not None:
            data.append(meta['annotation']) # 0..1

        data.extend(section_parsed.content)

        return _e('section', None, *data)
