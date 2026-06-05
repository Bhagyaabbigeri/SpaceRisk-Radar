import math
from typing import List, Dict, Any, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def haversine_3d(lat1: float, lon1: float, alt1: float, lat2: float, lon2: float, alt2: float) -> float:
    """
    Calculates the 3D distance between two points in kilometers.
    
    It first computes the 2D great-circle distance along the Earth's surface 
    using the Haversine formula, and then applies the Pythagorean theorem 
    to incorporate the difference in altitudes.
    
    lat1, lon1: Coordinates of point 1 in degrees.
    alt1: Altitude of point 1 in kilometers.
    lat2, lon2: Coordinates of point 2 in degrees.
    alt2: Altitude of point 2 in kilometers.
    
    Returns: Distance in kilometers.
    """
    # Earth's mean radius in km
    R = 6371.0
    
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Standard 2D Haversine formula
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    d_2d = R * c
    
    # 3D distance incorporating altitude difference
    d_3d = math.sqrt(d_2d**2 + (alt1 - alt2)**2)
    return d_3d

def calculate_collision_probability(sat1: dict, sat2: dict, distance_km: float) -> dict:
    """
    Computes a dynamic collision probability and risk factors based on orbital parameters,
    speed, operator control capabilities, environment density, and inclinations.
    """
    # 1. Base log probability based on 3D distance (km)
    # At d=0, log10(Pc) = -2.0 (Pc = 0.01 or 1%). Drops exponentially with distance.
    base_score = -2.0 - 0.08 * distance_km

    # 2. Extract satellite properties
    speed1 = sat1.get("speed_kms") or 7.5
    speed2 = sat2.get("speed_kms") or 7.5
    orbit1 = sat1.get("orbit") or "LEO"
    orbit2 = sat2.get("orbit") or "LEO"
    op1 = sat1.get("operator") or ""
    op2 = sat2.get("operator") or ""
    inc1 = sat1.get("inclination") or 51.6
    inc2 = sat2.get("inclination") or 51.6
    c1 = sat1.get("country") or ""
    c2 = sat2.get("country") or ""

    # 3. Compute adjustments & risk factors
    factors = []
    
    if distance_km < 10.0:
        factors.append("Ultra-close proximity encounter (<10km)")
    elif distance_km < 50.0:
        factors.append("Close proximity encounter (<50km)")

    # Orbit congestion adjustment (LEO is higher risk)
    orbit_adj = 0.0
    if orbit1 == "LEO" or orbit2 == "LEO":
        orbit_adj = 0.3
        factors.append("LEO orbital density multiplier")
    elif orbit1 == "GEO" and orbit2 == "GEO":
        orbit_adj = -0.4
        factors.append("GEO synchronized spacing")

    # Velocity adjustment
    try:
        avg_speed = (float(speed1) + float(speed2)) / 2.0
    except (ValueError, TypeError):
        avg_speed = 7.5
        
    speed_adj = 0.05 * (avg_speed - 7.0)
    if avg_speed > 8.0:
        factors.append("High relative crossing velocity")

    # Operator capability (Debris cannot coordinate/maneuver)
    is_debris1 = "debris" in str(op1).lower() or "debris" in str(c1).lower() or "debris" in str(sat1.get("name", "")).lower()
    is_debris2 = "debris" in str(op2).lower() or "debris" in str(c2).lower() or "debris" in str(sat2.get("name", "")).lower()
    
    operator_adj = 0.0
    if is_debris1 or is_debris2:
        operator_adj = 0.6
        debris_names = []
        if is_debris1: debris_names.append(sat1.get("name", "Debris"))
        if is_debris2: debris_names.append(sat2.get("name", "Debris"))
        factors.append("Uncontrolled space debris element")
    else:
        operator_adj = -0.3
        factors.append("Active coordinated payloads")

    # Inclination crossing geometry (Polar orbits intersect at high relative speeds/angles)
    inc_adj = 0.0
    try:
        f_inc1 = float(inc1)
        f_inc2 = float(inc2)
        if 70.0 <= f_inc1 <= 110.0 and 70.0 <= f_inc2 <= 110.0:
            inc_adj = 0.4
            factors.append("Polar orbital intersection node")
    except (ValueError, TypeError):
        pass

    # 4. Final score & probability calculation
    final_score = base_score + orbit_adj + speed_adj + operator_adj + inc_adj
    # Clamp score to realistic range (10^-8 to 10^-1)
    final_score = max(-8.0, min(-1.0, final_score))
    prob = 10.0 ** final_score

    # Format percentage
    if prob >= 0.001:
        prob_pct = f"{prob * 100:.3f}%"
    else:
        prob_pct = f"{prob * 100:.6f}%"

    # Determine risk level
    if prob >= 0.001:
        level, color = "CRITICAL", "#ff3b30"
    elif prob >= 0.0001:
        level, color = "HIGH", "#ff7a00"
    elif prob >= 0.000001:
        level, color = "MEDIUM", "#ffcc00"
    else:
        level, color = "LOW", "#00f0ff"

    # Evasion Recommendation
    name1 = sat1.get("name", "Sat1")
    name2 = sat2.get("name", "Sat2")
    if is_debris1 and is_debris2:
        maneuver = "Collision risk is unmitigated; both tracking elements are passive debris particles."
    elif is_debris1:
        maneuver = f"Evasion recommended for {name2}: Execute prograde delta-V burn of +0.25 m/s."
    elif is_debris2:
        maneuver = f"Evasion recommended for {name1}: Execute prograde delta-V burn of +0.25 m/s."
    else:
        maneuver = f"Cooperative collision avoidance maneuver: {name1} thrust radial-in, {name2} thrust radial-out."

    return {
        "probability": prob,
        "probability_pct": prob_pct,
        "risk_level": level,
        "risk_color": color,
        "risk_factors": factors if factors else ["Baseline proximity risk"],
        "evasion_maneuver": maneuver
    }


def find_conjunctions(satellites: List[Union[Dict[str, Any], Any]], threshold_km: float = 500.0) -> List[Dict[str, Any]]:
    """
    Screens all pairs of satellites and flags those with a 3D distance less than threshold_km.
    
    satellites: A list of satellite dicts or objects. Each item must represent a satellite 
                and provide:
                - 'name'
                - 'latitude'
                - 'longitude'
                - 'altitude' or 'altitude_km'
    threshold_km: The distance threshold in km (default 500km).
    
    Returns: A list of dictionaries representing conjunction events, containing:
             - 'sat1': Name of first satellite
             - 'sat2': Name of second satellite
             - 'distance_km': The 3D distance in km
             - 'details': Detailed positions of both satellites
    """
    logger.info(f"Screening {len(satellites)} satellites for conjunctions under {threshold_km}km...")
    conjunctions = []
    num_sats = len(satellites)
    
    for i in range(num_sats):
        for j in range(i + 1, num_sats):
            sat1 = satellites[i]
            sat2 = satellites[j]
            
            # Robustly extract name, latitude, longitude, and altitude from dictionary or object
            name1 = sat1.get("name") if isinstance(sat1, dict) else getattr(sat1, "name", f"Sat_{i}")
            lat1 = sat1.get("latitude") if isinstance(sat1, dict) else getattr(sat1, "latitude", 0.0)
            lon1 = sat1.get("longitude") if isinstance(sat1, dict) else getattr(sat1, "longitude", 0.0)
            alt1 = sat1.get("altitude_km") or sat1.get("altitude") if isinstance(sat1, dict) else getattr(sat1, "altitude_km", getattr(sat1, "altitude", 0.0))
            
            name2 = sat2.get("name") if isinstance(sat2, dict) else getattr(sat2, "name", f"Sat_{j}")
            lat2 = sat2.get("latitude") if isinstance(sat2, dict) else getattr(sat2, "latitude", 0.0)
            lon2 = sat2.get("longitude") if isinstance(sat2, dict) else getattr(sat2, "longitude", 0.0)
            alt2 = sat2.get("altitude_km") or sat2.get("altitude") if isinstance(sat2, dict) else getattr(sat2, "altitude_km", getattr(sat2, "altitude", 0.0))
            
            # Compute 3D distance
            dist = haversine_3d(lat1, lon1, alt1, lat2, lon2, alt2)
            
            if dist < threshold_km:
                ai_risk = calculate_collision_probability(
                    sat1 if isinstance(sat1, dict) else sat1.__dict__,
                    sat2 if isinstance(sat2, dict) else sat2.__dict__,
                    dist
                )
                conjunctions.append({
                    "sat1": name1,
                    "sat2": name2,
                    "distance_km": round(dist, 2),
                    "probability": ai_risk["probability"],
                    "probability_pct": ai_risk["probability_pct"],
                    "risk_level": ai_risk["risk_level"],
                    "risk_color": ai_risk["risk_color"],
                    "risk_factors": ai_risk["risk_factors"],
                    "evasion_maneuver": ai_risk["evasion_maneuver"],
                    "details": {
                        "sat1_pos": {"lat": round(lat1, 4), "lon": round(lon1, 4), "alt": round(alt1, 2)},
                        "sat2_pos": {"lat": round(lat2, 4), "lon": round(lon2, 4), "alt": round(alt2, 2)}
                    }
                })
                
    logger.info(f"Screening complete. Found {len(conjunctions)} conjunctions.")
    return conjunctions

if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path to allow absolute package imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from backend.tle_fetcher import get_tles
        from backend.orbit_calculator import calculate_orbit_state
        
        print("Running Conjunction Risk Engine Self-Test/Integration...")
        
        # 1. Fetch TLE data (loads automatically from cache)
        tles = get_tles()
        
        if not tles:
            print("\n[Warning] No TLEs loaded from cache. Using simulated data.")
            satellites = [
                {"name": "ISS (ZARYA)", "latitude": 50.22, "longitude": 6.59, "altitude": 423.7},
                {"name": "Simulated Debris A", "latitude": 50.15, "longitude": 6.50, "altitude": 425.0}, # Closer than 500km
                {"name": "HST (Hubble)", "latitude": 28.46, "longitude": 34.28, "altitude": 540.0}
            ]
        else:
            print(f"Propagating {len(tles)} active TLEs to current positions...")
            satellites = []
            for tle in tles:
                try:
                    state = calculate_orbit_state(tle.line1, tle.line2)
                    satellites.append({
                        "name": tle.name,
                        "latitude": state.latitude,
                        "longitude": state.longitude,
                        "altitude_km": state.altitude_km
                    })
                except Exception as pe:
                    logger.warning(f"Skipped propagation of {tle.name}: {pe}")
                    
        # 2. Add a simulated close debris near the first satellite to guarantee a conjunction event for testing
        if satellites:
            first_sat = satellites[0]
            # Place a dummy debris particle just 150 km away
            satellites.append({
                "name": "TEST_DEBRIS_X",
                "latitude": first_sat["latitude"] + 0.8,
                "longitude": first_sat["longitude"] + 0.8,
                "altitude_km": first_sat["altitude_km"] + 10.0
            })
            
        # 3. Perform screening
        threshold = 500.0
        conjunctions = find_conjunctions(satellites, threshold_km=threshold)
        
        # 4. Display findings
        print(f"\n=== Conjunction Screening Results (Threshold: {threshold} km) ===")
        if conjunctions:
            for index, c in enumerate(conjunctions, 1):
                print(f"\n[{index}] RISK ALERT: {c['sat1']} <---> {c['sat2']}")
                print(f"    Calculated 3D Distance: {c['distance_km']} km")
                print(f"    Positions:")
                print(f"      - {c['sat1']}: Lat {c['details']['sat1_pos']['lat']} deg, Lon {c['details']['sat1_pos']['lon']} deg, Alt {c['details']['sat1_pos']['alt']} km")
                print(f"      - {c['sat2']}: Lat {c['details']['sat2_pos']['lat']} deg, Lon {c['details']['sat2_pos']['lon']} deg, Alt {c['details']['sat2_pos']['alt']} km")
        else:
            print("No risk conjunctions detected under 500km threshold.")
            
        # 5. Showcase distance checks for active pairs
        print("\n=== Distance Breakdown Example (First 3 Pairs) ===")
        demo_pairs = []
        for i in range(min(len(satellites), 3)):
            for j in range(i + 1, min(len(satellites), 3)):
                dist = haversine_3d(
                    satellites[i]["latitude"], satellites[i]["longitude"], satellites[i]["altitude_km"],
                    satellites[j]["latitude"], satellites[j]["longitude"], satellites[j]["altitude_km"]
                )
                print(f"Distance between {satellites[i]['name']} and {satellites[j]['name']}: {dist:.2f} km")
                
    except Exception as e:
        print(f"Execution failed: {e}")
