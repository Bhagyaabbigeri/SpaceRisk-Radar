import time, urllib.request, json, sys

url = 'http://127.0.0.1:5000/api/objects'
for i in range(20):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            objs = json.load(r)
            print('COUNT:', len(objs))
            for o in objs[:5]:
                print('-', o.get('name'))
            sys.exit(0)
    except Exception as e:
        print('retry', i, str(e))
        time.sleep(1)
print('FAILED')
sys.exit(1)
