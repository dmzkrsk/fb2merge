# coding=utf-8
from . import fb2tag
import re
from .xpath import SRC_TITLE_INFO, TITLE_INFO

def extract_year(tree):
    dates = []
    for ti in [TITLE_INFO, SRC_TITLE_INFO]:
        ti_item = ti(tree)
        if not ti_item:
            continue

        dates.extend(
            filter(None, (x.attrib.get('value', x.text) for x in ti_item[0] if x.tag == fb2tag('date')))
        )

    xy = lambda x: max(map(int, re.split('\D+', x)))
    dv = filter(None, map(xy, dates))
    return min(dv) if dv else None

def fb2title(title):
    tr = []
    for p in title:
        if p.tag != fb2tag('p'):
            continue

        ptext = p.text + ''.join((sub.text or '') + (sub.tail or '') for sub in p)
        ptext = ptext.strip()
        tr.append(ptext)

    return '. '.join(tr)
