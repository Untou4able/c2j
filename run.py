import os
import re
import subprocess
import sys


import ipaddress
import rrdtool


import router
import snmp


if len(sys.argv) < 2:
  print 'Usage: %s ip_address [ip_address [...]]' % sys.argv[0]
  exit(1)

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


ips = sys.argv[1:]
data = {}
vrfs = set()
reg = re.compile('[0-9]{10,}')
for ip in ips:
  data[ip] = {}
  data[ip]['questionableIntfs'] = {}
  getFileNameCmd = ['ssh', 'rs', 'grep "ip address %s" /tftpboot/cisco/* | cut -f 1 -d":"' % ip]
  data[ip]['cfgFileName'] = subprocess.check_output(getFileNameCmd).strip()
  scpcfgcmd = 'scp rs:%s %s' % (data[ip]['cfgFileName'], TMPDIR)
  scpmrtgcmd = 'scp imota:/var/www/data/mrtgrrd/data/%s/* %s' % (ip, TMPDIR)
  subprocess.check_output(scpcfgcmd.split())
  subprocess.check_output(scpmrtgcmd.split())

  data[ip]['cfgFile'] = open(TMPDIR + os.path.basename(data[ip]['cfgFileName']))
  data[ip]['snmpIntfs'] = snmp.getIntfs(ip)
  data[ip]['router'] = router.Router(data[ip]['cfgFile'])

  data[ip]['cfgFile'].close()

  for intfName in data[ip]['router'].interfaces.keys():
    intf = data[ip]['router'].interfaces.get(intfName)
    if not intf.vrf:
      data[ip]['router'].interfaces.pop(intfName)
      continue
    if not reg.search(intf.description):
      data[ip]['questionableIntfs'][intfName] = data[ip]['router'].interfaces.pop(intfName)
  vrfs.update([intf.vrf for intf in data[ip]['router'].interfaces.values()])

for ip in ips:
  for intfName in data[ip]['questionableIntfs'].keys():
    if data[ip]['questionableIntfs'][intfName] in vrfs:
      data[ip]['router'].interfaces[intfname] = data[ip]['questionableIntfs'].pop(intfName)

for ip in ips:
  printout(ip, data[ip]['router'].interfaces.values(), data[ip]['router'].statics, data[ip]['snmpIntfs'])
