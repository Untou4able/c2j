import pexpect
import sys


login = 'untou4able'
password = '0dc3d9c0'
ip = '195.112.224.10'
promt = '#'

intfs = ['Gi0/1.618499', 'Gi0/1.756304']
c = pexpect.spawn('ssh %s@%s' % (login, ip), logfile=sys.stdout)
r = c.expect(['word:', 'yes/no'])
if r == 1:
  c.sendline('yes')
c.sendline(password)
c.expect(promt)
c.sendline('conf t')
c.expect(promt)
for intf in intfs:
  c.sendline('interface %s' % intf)
  c.expect(promt)
  c.sendline('shutdown')
  c.expect(promt)
c.sendline('end\rexit')
c.expect('closed')
