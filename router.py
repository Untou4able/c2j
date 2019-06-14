import filereader
import filters


class Router(object):

  def __init__(self, f):
    self._byVrf = {}
    fileReader = filereader.FileReader(f)
    self._interfaceFilter = filters.InterfaceFilter()
    self._staticFilter = filters.StaticFilter()
    fileReader.addFilter(self._interfaceFilter)
    fileReader.addFilter(self._staticFilter)
    fileReader.read()
    #self._rearrangeByVrf()

  def __getitem__(self, key):
    return self._interfaceFilter.matches.get(key)

  @property
  def interfaces(self):
    return self._interfaceFilter.matches

  @property
  def statics(self):
    return self._staticFilter.matches

  @property
  def vrfs(self):
    if not self._byVrf:
      self._rearrangeByVrf()
    return self._byVrf

  def _rearrangeByVrf(self):
    for i in self.interfaces:
      interface_vrf = self.interfaces[i].vrf
      vrf = self._byVrf.setdefault(interface_vrf, {})
      vrf[i] = self.interfaces[i]


if __name__ == '__main__':
  import pickle
  from pprint import pprint
  r = Router(open('/tmp/PE-006-01.krasnet.ru.cfg'))
  pickle.dump(r, open('.test', 'wb'))
  pprint(r.vrfs)
