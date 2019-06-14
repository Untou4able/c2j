import pickle
import sys


import ipaddress


from run import RouterData
import jintfs


class MoveVrf(object):

  _defaultStartIndex = 1000

  def __init__(self, cvrf, jvrf, statics, trouters):
    self._intfIndexes = {}
    self._cvrf = cvrf
    self._jvrf = jvrf
    self._jvrfid = self._jvrf.split('-')[0].replace('v', '')
    self._jvrfdesc = self._jvrf.split('-')[1]
    self._statics = statics

  def moveIntf(self, cintf):
    tintflist = self._trouter.intfsByVlan.get(cintf.vlanOuter)
    if not tintflist:
      tintf = self._defaultIntf
      unit = self._intfIndexes[self._defaultIntf]
      self._intfIndexes[self._defaultIntf] += 1
    else:
      for tintf in tintflist:
        if 'xe' in tintf:
          break
      unit = self._intfIndexes.setdefault(tintf, self._defaultStartIndex)
      while unit in self._trouter.unitList[tintf]:
        unit += 1
    jintf = '%s.%s' % (tintf, unit)
    self._intfIndexes[tintf] = unit + 1
    statics = self._gethops(cintf.ip)
    return InterfaceMoving(cintf, self._jvrf, jintf, statics)

  def _gethops(self, ips):
    hops = {}
    for ip in ips:
      ipaddr = ipaddress.IPv4Interface(unicode(ip.replace(' ', '/')))
      hops = {host: self._statics[host] for host in ipaddr.network.hosts() if host in self._statics}
    return hops

  def jvrfconf(self):
    jvrfconf = 'set routing-instances %s description " ### VPN: %s ### "\n' % (self._jvrf, self._jvrfdesc)
    jvrfconf += 'set routing-instances %s instance-type vrf\n' % self._jvrf
    jvrfconf += 'set routing-instances %s route-distinguisher 12389:%s\n' % (self._jvrf, self._jvrfid)
    jvrfconf += 'set routing-instances %s vrf-target import target:12389:%s\n' % (self._jvrf, self._jvrfid)
    jvrfconf += 'set routing-instances %s vrf-target export target:12389:%s\n' % (self._jvrf, self._jvrfid)
    jvrfconf += 'set routing-instances %s vrf-table-label' % self._jvrf
    return jvrfconf


class StaticRoutes(object):
  pass

class InterfaceMoving(object):

  _cpolicytojpolicy = {
    '100Mb': 'lim100m',
    '1024k': 'lim1m',
    '10Mbit': 'lim10m',
    '128k': 'lim128k',
    '14Mbit': 'lim14m',
    '1Mbit': 'lim1m',
    '1Mbit.in': 'lim1m',
    '20Mbit': 'lim20m',
    '20Mbps': 'lim20m',
    '256k': 'lim256k',
    '2M': 'lim2m',
    '2Mbit': 'lim2m',
    '30Mbit': 'lim30m',
    '3Mbit': 'lim3m',
    '4096k': 'lim4m',
    '4Mbit': 'lim4m',
    '50Mbit': 'lim50m',
    '512Kbit': 'lim512k',
    '512k': 'lim512k',
    '512out': 'lim512k',
    '5Mbit': 'lim5m',
    '6144k': 'lim6k',
    '64k': 'lim64k',
    '6MB': 'lim6m',
    '6Mbit': 'lim6m',
    '8Mbit': 'lim8m',
    '8Mbps': 'lim8m',
    'FPSU': 'lim64k',
    'Mbit': 'lim1m',
    'OU': 'lim128k',
    'OU_256': 'lim256k',
    'OU_512': 'lim512k',
    'PM_10M': 'lim10m',
    'PM_1M': 'lim1m',
    'PM_20M': 'lim20m',
    'PM_4M': 'lim4m',
    'PM_8M': 'lim8m',
    'PVDNP-MainChannel': 'lim512k',
    'PVDNP-RezervChannel': 'lim128k'
  }

  def __init__(self, intf, jvrf, jintf, statics):
    self._intf = intf
    self._jvrf = jvrf
    self._jintf = jintf
    self._statics = statics
    self._set = 'set interface %s' % self._jintf

  def nointf(self):
    ips = []
    configList = ['interface ' + self._intf.name]
    for line in reversed(self._intf.config.split('\n')):
      line = line.strip()
      if line.startswith('ip address '):
        ips.append(line)
      else:
        if ips:
          ips.reverse()
          for ip in ips:
            configList.append('no ' + ip);
          ips = []
        elif not line.startswith('no ') and not 'cdp' in line:
          configList.append('no ' + line)
    return '\n'.join(configList)

  def jconf(self):
    jintfconf = []
    jintfconf.append(self._makeDescription())
    jintfconf.append(self._makeEncapsulation())
    jintfconf.append(self._makeIps())
    if self._intf.policyInput or self._intf.policyOutput:
      jintfconf.append(self._addPolicies())
    jintfconf.append(self._addToRoutingInstance())
    return '\n'.join(jintfconf)

  def addOuterVlanToInterfaceOnEx(self):
    return 'set interfaces xe-4/0/5 unit 0 family ethernet-switching vlan members %s' % self._intf.vlanOuter

  def noStatics(self):
    routes = []
    for hop in self._statics:
      for route in self._statics[hop]:
        routes.append('no ip route vrf %s %s %s' % (self._intf.vrf, route.with_netmask.replace('/', ' '), hop))
    return '\n'.join(routes)

  def jstatics(self):
    routes = []
    for hop in self._statics:
      for route in self._statics[hop]:
        routes.append('set routing-instances %s routing-options static route %s next-hop %s' % (self._jvrf, route, hop))
    return '\n'.join(routes)

  def _makeDescription(self):
    desc = '"## VPN: %s; %s"' % (self._jvrf, self._intf.description)
    return 'set interface %s description %s' % (self._jintf, desc)

  def _makeEncapsulation(self):
    if self._intf.vlanInner:
      return self._set + ' vlan-tags outer %s inner %s' % (self._intf.vlanOuter, self._intf.vlanInner)
    else:
      return self._set + ' vlan-id %s' % self._intf.vlanOuter

  def _makeIps(self):
    ipstr = ' family inet address %s'
    ips = []
    for ip in self._intf.ip:
      ip = unicode(ip).replace(' ', '/')
      ips.append(self._set + ipstr % str(ipaddress.IPv4Interface(ip).with_prefixlen))
    return '\n'.join(ips)

  def _addPolicies(self):
    policyList = []
    policyStr = '%s family inet policer %s %s'
    jinputPolicy = self._cpolicytojpolicy.get(self._intf.policyInput)
    if jinputPolicy:
      policyList.append(policyStr %(self._set, 'input', jinputPolicy))
      jinputPolicy = jinputPolicy.replace('lim', '')
    joutputPolicy = self._cpolicytojpolicy.get(self._intf.policyOutput)
    if joutputPolicy:
      policyList.append(policyStr %(self._set, 'output', joutputPolicy))
      joutputPolicy = joutputPolicy.replace('lim', '')
    if jinputPolicy or joutputPolicy:
      policyList.append('%s bandwidth %s' % (self._set, jinputPolicy or joutputPolicy))
    return '\n'.join(policyList)


  def _addToRoutingInstance(self):
    return 'set routing-instances %s interface %s' % (self._jvrf, self._jintf)
    

if not len(sys.argv) == 5:
  print '\n\tUSAGE: python %s \033[4mold_vrf\033[0m n\033[4mew_vrf\033[0m' % __file__
  print '\t\t\033[4mold_vrf\033[0m Cisco vrf name'
  print '\t\t\033[4mnew_vrf\033[0m Juniper routing-instance name'
  exit()

cvrf = sys.argv[1]
jvrf = sys.argv[2]
_trouters = [
  'KRSN-BPE1',
  'KRSN-BPE2'
]
from pprint import pprint

ips = pickle.load(open('.iplist'))
data = pickle.load(open('.data'))
statics = {}
for ip in data:
  routes = data[ip].router.statics.get(cvrf)
  if routes:
    statics.update(routes)

moveVrf = MoveVrf(cvrf, jvrf, statics)
print moveVrf.jvrfconf()

for ip in ips:
  r = data.get(ip)
  if cvrf in r.router.vrfs:
    print ip
    for intf in r.router.vrfs[cvrf].values():
      i = moveVrf.moveIntf(intf)
      print i.nointf()
      #i.nointf()
      print i.noStatics()
      if not intf.shutdown and intf.ip:
        print i.jconf()
        print i.jstatics()
        print i.addOuterVlanToInterfaceOnEx()
      print '=' * 40
