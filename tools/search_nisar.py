import urllib.request, urllib.error, json
url='http://127.0.0.1:5000/api/search?q=NISAR'
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        body = r.read().decode('utf-8')
        print('STATUS', getattr(r,'status',None))
        print(body)
except urllib.error.HTTPError as e:
    print('HTTPError', e.code)
    try:
        print(e.read().decode('utf-8'))
    except Exception:
        pass
except Exception as e:
    print('ERR', e)
