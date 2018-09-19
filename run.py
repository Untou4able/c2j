import os
import subprocess
import sys


import ipaddress
import rrdtool


import router
import snmp


if len(sys.argv) < 2:
  print 'Usage: %s ip_address' % sys.argv[0]
  exit(1)

def monthMaxAvg(f):
  r = rrdtool.fetch(f, 'MAX', '-s', '-30d')
  legitValues = [i[0] for i in r[2] if not i[0] is None]
  inp = sum(legitValues) / len(legitValues)
  legitValues = [i[1] for i in r[2] if not i[1] is None]
  out = sum(legitValues) / len(legitValues)
  return (inp, out)

TMPDIR = '/tmp/'
ip = sys.argv[1]
getFileNameCmd = ['ssh', 'rs', 'grep "ip address %s" /tftpboot/cisco/* | cut -f 1 -d":"' % ip]
cfgFileName = '/tmp/PE-006-01.krasnet.ru.cfg'
cfgFileName = subprocess.check_output(getFileNameCmd).strip()
scpcfgcmd = 'scp rs:%s %s' % (cfgFileName, TMPDIR)
scpmrtgcmd = 'scp imota:/var/www/data/mrtgrrd/data/%s/* %s' % (ip, TMPDIR)
subprocess.check_output(scpcfgcmd.split())
subprocess.check_output(scpmrtgcmd.split())

cfgFile = open(TMPDIR + os.path.basename(cfgFileName))
outFile = open(ip + '.csv', 'w')

outFile.write('interface;description;out vlan;inner vlan;ip;vrf;shutdown;input policy;output policy;input traffic;output traffic;static routes\n')
snmpIntfs = snmp.getIntfs(ip)
router = router.Router(cfgFile)

for intf in router.interfaces.values():
  inp = ''
  out = ''
  statics = []
  snmpIndex = snmpIntfs.get(intf.name)
  if snmpIndex:
    try:
      rrdFileName = '%s%s_%s.rrd' % (TMPDIR, ip, snmpIndex)
      inp, out = monthMaxAvg(rrdFileName)
    except:
      pass
  for address in intf.ip:
    address = ipaddress.IPv4Interface(unicode(address.replace(' ', '/')))
    vrfRoutes = router.statics.get(intf.vrf)
    if vrfRoutes:
      for i in address.network.hosts():
        static = vrfRoutes.get(i)
        if static:
          for s in static:
            statics.append('no ip route vrf %s %s %s %s' % (intf.vrf, s.network_address, s.netmask, i))
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
    ','.join(statics)
  ))

cfgFile.close()
outFile.close()
