import random
import requests
import pprint
import json


url = 'http://10.128.142.5:8888/api_jsonrpc.php'
sid = random.randint(1, 100)
api_user = {'user': 'api', 'password': 'Fgbkmctw'}
auth_data = {'jsonrpc': '2.0', 'method': 'user.login', 'params': api_user, 'id': sid}
api_login = requests.post(url, json=auth_data)
auth = api_login.json()['result']
data = {
  'jsonrpc': '2.0',
  'auth': auth,
  'id': sid,
  'method': 'host.get',
  'params': {
    'groupids': 141
    #'interfaceids': '19243'
  }
}

res = requests.post(url, json=data)
pprint.pprint(json.loads(res.text))
