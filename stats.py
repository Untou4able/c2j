from pprint import pprint


ips = [
  '195.112.224.9',
  '195.112.224.10',
  '195.112.224.11',
  '195.112.224.12',
  '195.112.224.14',
  '195.112.224.16',
  '195.112.224.44',
  '195.112.224.49',
  '195.112.224.43',
  #'195.112.224.36',
  '195.112.224.26',
  '195.112.224.18',
  #'195.112.224.45',
  '195.112.224.24',
  '195.112.224.47',
  '195.112.224.21',
  '195.112.224.42',
  '195.112.224.23'
]

vrfs = {}

for ip in ips:
  print ip
  r = open(ip + '.csv')
  r = r.read().strip().split('\n')
  for line in r[1:]:
    line = line.split(';')
    #if not line[5] or not line[9] or line[9] == '0.0':
    #  continue
    #else:
    vrf = vrfs.setdefault(line[5], {})
    vrf.setdefault(ip, 0)
    vrf[ip] += 1

stats = open('stats.csv', 'w')
stats.write('VPN;' + ';'.join(ips) + ';total\n')
for vrf in vrfs:
  stats.write(vrf + ';')
  for ip in ips:
    try:
      stats.write(str(vrfs[vrf][ip]) + ';')
    except:
      stats.write('0;')
  stats.write(str(sum(vrfs[vrf].values())) + '\n')
stats.close()
