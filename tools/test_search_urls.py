import urllib.request, urllib.error
urls=[
    'http://127.0.0.1:5000/api/search?q=NISAR',
    'http://127.0.0.1:5000/api/search/?q=NISAR',
    'http://127.0.0.1:5000/api/search'
]
for url in urls:
    try:
        print('URL',url)
        r=urllib.request.urlopen(url, timeout=5)
        print('OK', getattr(r,'status',None))
        print(r.read().decode()[:800])
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, url)
        try:
            print(e.read().decode())
        except Exception:
            pass
    except Exception as e:
        print('ERR', e, url)
