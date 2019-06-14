import os
import pickle
import re
import subprocess


import ipaddress
import rrdtool


import router
import snmp


TMPDIR = '/tmp/'


def printout(ip, intfs, statics, snmpIntfs):
  outFile = open(ip + '.csv', 'w')
  outFile.write('interface;description;out vlan;inner vlan;ip;vrf;shutdown;input policy;output policy;input traffic;output traffic;static routes\n')
  for intf in intfs:
    inp = ''
    out = ''
    routes = []
    snmpIndex = snmpIntfs.get(intf.name)
    if snmpIndex:
      try:
        rrdFileName = '%s%s_%s.rrd' % (TMPDIR, ip, snmpIndex)
        inp, out = monthMaxAvg(rrdFileName)
      except:
        pass
    for address in intf.ip:
      address = ipaddress.IPv4Interface(unicode(address.replace(' ', '/')))
      vrfRoutes = statics.get(intf.vrf)
      if vrfRoutes:
        for i in address.network.hosts():
          route = vrfRoutes.get(i)
          if route:
            for r in route:
              routes.append('hop: %s net:%s' % (i, r))
    outFile.write('%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n' % (
      intf.name,
      intf.description,
      intf.vlanOuter,
      intf.vlanInner,
      ','.join(intf.ip),
      intf.vrf,
      intf.shutdown,
      intf.policyInput,
      intf.policyOutput,
      inp,
      out,
      ','.join(routes)
    ))
  outFile.close()


def monthMaxAvg(f):
  r = rrdtool.fetch(f, 'MAX', '-s', '-30d')
  legitValues = [i[0] for i in r[2] if not i[0] is None]
  inp = sum(legitValues) / len(legitValues)
  legitValues = [i[1] for i in r[2] if not i[1] is None]
  out = sum(legitValues) / len(legitValues)
  return (inp, out)


class RouterData(object):

  TMPDIR = '/tmp/'

  @property
  def ip(self):
    return self._ip

  @property
  def cfgRmtPath(self):
    return self._cfgRmtPath

  @property
  def cfgLocPath(self):
    return self.TMPDIR + os.path.basename(self._cfgRmtPath)

  @property
  def snmpIntfs(self):
    return self._snmpIntfs

  @property
  def router(self):
    return self._router

  @property
  def snmpIntfs(self):
    return self._snmpIntfs

  def __init__(self, ip):
    self._ip = ip
    self._getCfg()
    self._getMrtg()
    cfgFile = open(self.cfgLocPath)
    self._router = router.Router(cfgFile)
    cfgFile.close()
    self._snmpIntfs = snmp.getIntfs(ip)

  def _getCfg(self):
    getFileNameCmd = ['ssh', 'rs', 'grep "ip address %s" /tftpboot/cisco/* | cut -f 1 -d":"' % self.ip]
    self._cfgRmtPath = subprocess.check_output(getFileNameCmd).strip()
    if not self._cfgRmtPath:
      raise IOError('Config file not found for %s' % self.ip)
    scpcfgcmd = 'scp rs:%s %s' % (self._cfgRmtPath, self.TMPDIR)
    subprocess.check_output(scpcfgcmd.split())

  def _getMrtg(self):
    try:
      scpmrtgcmd = 'scp imota:/var/www/data/mrtgrrd/data/%s/* %s' % (self.ip, self.TMPDIR)
      subprocess.check_output(scpmrtgcmd.split())
    except:
      pass


if __name__ == '__main__':
  ips = [
    '195.112.224.26',
    '195.112.224.43',
    '195.112.224.36',
    '195.112.224.18',
    '195.112.224.45',
    '195.112.224.24',
    '195.112.224.47',
    '195.112.224.21',
    '195.112.224.42',
    '195.112.224.23',
    '195.112.224.12',
    '195.112.224.11',
    '195.112.224.14',
    '195.112.224.16',
    '195.112.224.44',
    '195.112.224.49',
    '195.112.224.10',
    '195.112.224.9'
  ]
  iplistPickleFile = open('.iplist', 'w')
  dataPickleFile = open('.data', 'w')
  vrfPickleFile = open('.vrfs', 'w')
  data = {}
  vrfs = set()
  for ip in ips[:]:
    print ip
    try:
      data[ip] = RouterData(ip)
    except IOError as e:
      ips.remove(ip)
      print e
      continue
    #print data[ip].router.vrfs
  
    for intfName in data[ip].router.interfaces.keys():
      intf = data[ip].router.interfaces.get(intfName)
      if not intf.vrf:
        data[ip].router.interfaces.pop(intfName)
        continue
    vrfs.update([intf.vrf for intf in data[ip].router.interfaces.values()])
  
  for ip in ips:
    printout(ip, data[ip].router.interfaces.values(), data[ip].router.statics, data[ip].snmpIntfs)

  pickle.dump(ips, iplistPickleFile)
  pickle.dump(data, dataPickleFile)
  pickle.dump(vrfs, vrfPickleFile)
  iplistPickleFile.close()
  dataPickleFile.close()
  vrfPickleFile.close()
