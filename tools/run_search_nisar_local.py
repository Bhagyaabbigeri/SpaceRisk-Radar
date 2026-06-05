import sys, os
from datetime import datetime, timezone
sys.path.append(r'D:\Collision-Risk-Visualizer')
from backend.tle_fetcher import get_tles
from backend.orbit_calculator import calculate_orbit_state

q='NISAR'
print('Loading TLEs...')
tles = get_tles()
print('Total TLEs:', len(tles))
found = []
for i,t in enumerate(tles):
    if t.name and q.lower() in t.name.lower():
        found.append((i,t))
        break

if not found:
    print('No matching TLE found for', q)
    sys.exit(0)

idx,tle = found[0]
print('Found at index', idx, 'name=', tle.name)
dt = datetime.now(timezone.utc)
state = calculate_orbit_state(tle.line1, tle.line2, dt)
print('Time:', dt.isoformat())
print('Latitude:', state.latitude)
print('Longitude:', state.longitude)
print('Altitude_km:', state.altitude_km)
print('Speed_kms:', state.speed_kms)
