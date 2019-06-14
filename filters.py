import re


import ipaddress


import interface


class Filter(object):

  def __init__(self):
    self._matches = {}

  @property
  def matches(self):
    return self._matches


class InterfaceFilter(Filter):

  def __init__(self):
    super(InterfaceFilter, self).__init__()
    self._intfStarted = False
    self._intf = None

  def line(self, line):
    if line.strip() == '!':
      self._intfStarted = False
      if self._intf:
        self._matches[self._intf.name] = self._intf
        self._intf = None
        return True
      return False
    if line.startswith('interface'):
      self._intfStarted = True
      self._intf = interface.Interface()
      self._intf.parameterFromString(line)
      return True
    if self._intfStarted:
      self._intf.parameterFromString(line)
      return True
    return False


class InterfaceFilterPort(InterfaceFilter):

  def __init__(self):
    super(InterfaceFilterPort, self).__init__()
    self._re = re.compile('(.*?)([0-9]{9,12})(.*)')

  def line(self, line):
    if line.strip() == '!':
      self._intfStarted = False
      if self._intf:
        self._matches[self._intf.name] = self._intf
        self._intf = None
        return True
      return False
    if line.startswith('interface'):
      self._intfStarted = True
      self._intf = interface.Interface()
      self._intf.parameterFromString(line)
      return True
    if self._intfStarted:
      if line.strip().startswith('description'):
        r = self._re.search(line)
        if not r:
          self._intfStarted = False
          self._intf = None
          return True
        else:
          if len(r.groups()[1]) == 9:
            newLine = r.groups()[0] + '1' + r.groups()[1] + r.groups()[2]
            self._intf.parameterFromString(newLine)
            return True
      self._intf.parameterFromString(line)
      return True
    return False


class StaticFilter(Filter):

  def line(self, line):
    if line.startswith('ip route vrf'):
      try:
        spline = line.split()
        vrf = spline[3]
        hop = ipaddress.IPv4Address(unicode(spline[6]))
        net = ipaddress.IPv4Network(unicode('/'.join(spline[4:6])))
        mvrf = self._matches.setdefault(vrf, {})
        mhop = mvrf.setdefault(hop, [])
        mhop.append(net)
        return True
      except:
        pass
    return False
