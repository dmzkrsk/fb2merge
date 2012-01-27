# coding=utf-8
from . import fb2tag

def fb2title(title):
    tr = []
    for p in title:
        if p.tag != fb2tag('p'):
            continue

        ptext = p.text + ''.join((sub.text or '') + (sub.tail or '') for sub in p)
        ptext = ptext.strip()
        tr.append(ptext)

    return '. '.join(tr)
