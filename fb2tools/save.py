# coding=utf-8
from zipfile import ZipFile, ZIP_DEFLATED

class Saver(object):
    def __init__(self, filename):
        self._f = filename

    def save(self, xml):
        raise NotImplementedError()

class SaveXml(Saver):
    def save(self, xml):
        with open(self._f, 'w') as f:
            f.write(xml)

class SaveZip(Saver):
    def __init__(self, filename, zip_filename):
        super(SaveZip, self).__init__(filename)
        self._z = zip_filename

    def save(self, xml):
        z = ZipFile(self._f, 'w', ZIP_DEFLATED)
        z.writestr(self._z, xml)
        z.close()
