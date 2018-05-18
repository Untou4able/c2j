class Interface(object):
  _name = ''
  _descirption = ''
  _vlanInner = ''
  _vlanOuter = ''
  _ip = []
  _vrf = ''
  _shutdown = ''
  _policyInput = ''
  _policyOutput = ''
  _string = ''

  def __init__(self, string = ''):
    if string:
      self.fromString(string)
      
  @property
  def name(self):
    return self._name

  @property
  def description(self):
    return self._descirption

  @property
  def vlanOuter(self):
    return self._vlanOuter

  @property
  def vlanInner(self):
    return self._vlanInner

  @property
  def config(self):
    return self._string.strip()

  @property
  def ip(self):
    return self._ip

  @property
  def shutdown(self):
    return self._shutdown

  @property
  def vrf(self):
    return self._vrf

  @property
  def policyInput(self):
    return self._policyInput

  @property
  def policyOutput(self):
    return self._policyOutput

  def fromString(self, s):
    for line in s.split('\n'):
      self.parameterFromString(line)

  def parameterFromString(self, line):
    self._string += '\n' in line and line or line + '\n'
    line = line.strip()
    if line.startswith('interface'):
      self._name = line.split()[1]
      return
    if line.startswith('description'):
      self._descirption = ' '.join(line.split()[1:])
      return
    if line.startswith('encapsulation dot1Q'):
      line = line.split()
      self._vlanOuter = line[2]
      if len(line) > 3:
        self._vlanInner = line[4]
      return
    if line.startswith('ip vrf forwarding'):
      self._vrf = line.split()[3]
      return
    if line.startswith('ip address'):
      if not self._ip:
        self._ip = []
      ip, mask = line.split()[2:4]
      self._ip.append('%s %s' % (ip, mask))
      return
    if line == 'shutdown':
      self._shutdown = line
      return
    if line.startswith('service-policy input'):
      self._policyInput = line.split()[2]
      return
    if line.startswith('service-policy output'):
      self._policyOutput = line.split()[2]
      return
