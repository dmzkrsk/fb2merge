# coding=utf-8
from fb2tools import fb2tag

class Formatter(object):
    def format(self, data):
        raise NotImplementedError()

class SimpleAuthorFormatter(Formatter):
    def format(self, authors):
        for a in authors:
            ao = {
                'first-name': '',
                'last-name': '',
                'middle-name': '',
                'nickname': '',
                }
            for t in a:
                for k in ao:
                    if t.tag == fb2tag(k):
                        ao[k] = (t.text or '').strip()
                        break

            nname = '%(last-name)s %(first-name)s %(middle-name)s' % ao
            nname = nname.strip()
            if not ao['nickname']:
                yield nname
                continue

            if nname:
                yield nname + ' (%(nickname)s)' % ao
            else:
                yield ao['nickname']
