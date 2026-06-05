import importlib
m = importlib.import_module('backend.app')
print('Module:', m)
print('Routes:', sorted([r.rule for r in m.app.url_map.iter_rules()]))
print('Has api_search func:', hasattr(m, 'api_search'))
