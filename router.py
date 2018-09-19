import filereader
import filters


class Router(object):

  def __init__(self, f):
    self._fileReader = filereader.FileReader(f)
    self._interfaceFilter = filters.InterfaceFilter()
    self._staticFilter = filters.StaticFilter()
    self._fileReader.addFilter(self._interfaceFilter)
    self._fileReader.addFilter(self._staticFilter)
    self._fileReader.read()

  def __getitem__(self, key):
    return self._interfaceFilter.matches.get(key)

  @property
  def interfaces(self):
    return self._interfaceFilter.matches

  @property
  def statics(self):
    return self._staticFilter.matches

if __name__ == '__main__':
  from pprint import pprint
  r = Router(open('/tmp/PE-006-01.krasnet.ru.cfg'))
  pprint(r.statics)
