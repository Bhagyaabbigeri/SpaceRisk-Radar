import urllib.request, sys
url='http://127.0.0.1:8000/index.html'
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        body = r.read().decode('utf-8')
        print('OK', len(body))
        print('HAS_SEARCH_INPUT:', 'id="search-name"' in body)
except Exception as e:
    print('ERR', e)
    sys.exit(1)
