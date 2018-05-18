from pysnmp.entity.rfc3413.oneliner import cmdgen


cmdGen = cmdgen.CommandGenerator()

def getIntfs(ip):
  intfs = {}
  r = cmdGen.nextCmd(cmdgen.CommunityData('public'),
                     cmdgen.UdpTransportTarget((ip, 161)),
                     '.1.3.6.1.2.1.2.2.1.2')
  for i in r[3]:
    _id = str(i[0][0]).split('.')[-1]
    name = str(i[0][1])
    intfs[name] = _id
  return intfs


if __name__ == '__main__':
  from pprint import pprint
  pprint(getIntfs('195.112.224.44'))
