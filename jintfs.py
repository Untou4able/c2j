class JIntfsByVlan(object):

  _routerIntfsDir = '/var/www/devlist/routers/'

  def __init__(self, router):
    self._router = router.upper()
    self._intfsByVlan = {}
    self._intfsUnitList = {}
    self._makeIntfs()

  def _makeIntfs(self):
    f = open(self._routerIntfsDir + self._router + '.list')
    for line in f:
      if not line.startswith('unit') and not line.startswith(' ') and not line.startswith('}'):
        line = line.split()
        intf = line[0].split('.')
        intfname = intf[0]
        unit = intf[1]
        outvlan = line[1]
        if '.' in outvlan:
          outvlan = outvlan.split('.')[1]
        intfset = self._intfsByVlan.setdefault(outvlan, set())
        intfset.add(intfname)
        unitlist = self._intfsUnitList.setdefault(intfname, [])
        unitlist.append(int(unit))
    f.close()

  @property
  def intfsByVlan(self):
    return self._intfsByVlan

  @property
  def unitList(self):
    return self._intfsUnitList

  def __repr__(self):
    return 'JIntfsByVlan(\'%s\')' % self._router


if __name__ == '__main__':
  from pprint import pprint
  bpe1 = JIntfsByVlan('krsn-bpe1')
  print bpe1
  #pprint(bpe1.intfsByVlan)
  pprint(bpe1.unitList)
