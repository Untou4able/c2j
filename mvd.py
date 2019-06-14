import re
import pickle
from run import RouterData


d = pickle.load(open('.data'))

f = open('mvd.csv', 'w')
for r in d:
  mvd = d[r].router.vrfs.get('VPN_135')
  if mvd:
    for i in mvd:
      i = mvd[i]
      desc = re.findall('\d{9,12}', i.description)
      if desc and i.ip:
        f.write('%s;%s\n' % (','.join(desc), ','.join(i.ip)))
f.close()
