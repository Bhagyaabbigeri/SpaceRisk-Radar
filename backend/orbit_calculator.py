import math
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Dict, Any, Optional
from sgp4.api import Satrec, jday, SGP4_ERRORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Satellite name to country mapping (common satellites)
SATELLITE_COUNTRY_MAP = {
    'ISS': 'USA/Russia',
    'HUBBLE': 'USA',
    'IRIDIUM': 'USA',
    'GLOBALSTAR': 'USA',
    'NOAA': 'USA',
    'GOES': 'USA',
    'INTELSAT': 'USA',
    'EUTELSAT': 'EU',
    'ASTRA': 'EU',
    'SPOT': 'France',
    'GLONASS': 'Russia',
    'ENVISAT': 'EU',
    'ARSAT': 'Argentina',
    'INSAT': 'India',
    'IRS': 'India',
    'FENGYUN': 'China',
    'BEIDOU': 'China',
    'YAOGAN': 'China',
    'ZIYUAN': 'China',
    'HAIYANG': 'China',
    'CHINASAT': 'China',
    'SHIJIAN': 'China',
}

# WGS-84 Earth Ellipsoid Constants
WGS84_A = 6378.137              # Semi-major axis in km
WGS84_F = 1.0 / 298.257223563   # Flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F)  # Semi-minor axis (~6356.7523142 km)
WGS84_E2 = 2.0 * WGS84_F - WGS84_F**2  # First eccentricity squared (~0.00669437999)
WGS84_EP2 = (WGS84_A**2 - WGS84_B**2) / (WGS84_B**2)  # Second eccentricity squared (~0.00673949674)

@dataclass
class OrbitState:
    latitude: float     # degrees, -90 to 90
    longitude: float    # degrees, -180 to 180
    altitude_km: float  # km above ellipsoid
    speed_kms: float    # km/s inertial speed
    timestamp: str      # ISO-8601 formatted UTC time string

    def to_dict(self) -> Dict[str, Any]:
        """Converts the OrbitState object to a dictionary."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_km": self.altitude_km,
            "speed_kms": self.speed_kms,
            "timestamp": self.timestamp
        }

def teme_to_lla(x: float, y: float, z: float, jd: float, fr: float) -> tuple[float, float, float]:
    """
    Converts Cartesian coordinates in TEME (True Equator, Mean Equinox) frame
    to Geodetic Latitude, Longitude, and Altitude using Greenwich Mean Sidereal Time (GMST) 
    and Bowring's closed-form ellipsoid method.
    
    x, y, z: Position coordinates in km.
    jd, fr: Julian Date components.
    
    Returns: (latitude_deg, longitude_deg, altitude_km)
    """
    # 1. Calculate Julian centuries since J2000.0
    t = (jd + fr - 2451545.0) / 36525.0
    
    # 2. Calculate Greenwich Mean Sidereal Time (GMST) in seconds (IAU 1982 formula)
    gmst_sec = 24110.54841 + 8640184.812866 * t + 0.093104 * t**2 - 6.2e-6 * t**3
    
    # Convert GMST to radians
    gmst_rad = (gmst_sec * math.pi / 43200.0) % (2.0 * math.pi)
    
    # 3. Rotate TEME coordinates to Earth-Centered Earth-Fixed (ECEF) coordinates
    # This is a clockwise rotation about the Z-axis (polar axis)
    x_ecef = x * math.cos(gmst_rad) + y * math.sin(gmst_rad)
    y_ecef = -x * math.sin(gmst_rad) + y * math.cos(gmst_rad)
    z_ecef = z
    
    # 4. Convert ECEF to Geodetic LLA using Bowring's closed-form method
    p = math.sqrt(x_ecef**2 + y_ecef**2)
    
    if p < 1e-9:
        # Handle polar singularity
        lat = 90.0 if z_ecef > 0.0 else -90.0
        lon = 0.0
        alt = abs(z_ecef) - WGS84_B
    else:
        theta = math.atan2(z_ecef * WGS84_A, p * WGS84_B)
        lat_rad = math.atan2(
            z_ecef + WGS84_EP2 * WGS84_B * math.sin(theta)**3,
            p - WGS84_E2 * WGS84_A * math.cos(theta)**3
        )
        lon_rad = math.atan2(y_ecef, x_ecef)
        
        # Radius of curvature in prime vertical
        N = WGS84_A / math.sqrt(1.0 - WGS84_E2 * math.sin(lat_rad)**2)
        alt = p / math.cos(lat_rad) - N
        
        lat = math.degrees(lat_rad)
        lon = math.degrees(lon_rad)
        
        # Normalize longitude to [-180, 180]
        lon = (lon + 180) % 360 - 180
        
    return lat, lon, alt

def get_inclination_from_tle(line2: str) -> float:
    """
    Extracts the inclination in degrees from TLE line 2.
    TLE line 2 format: Column 9-16 contains inclination in decimal degrees.
    
    Returns: Inclination in degrees (0-180)
    """
    try:
        # Columns 9-16 (0-indexed: 8-15) contain inclination
        if len(line2) >= 16:
            inclination_str = line2[8:16].strip()
            return float(inclination_str)
    except (ValueError, IndexError):
        logger.warning(f"Could not extract inclination from TLE line: {line2}")
    return 0.0

def parse_norad_id(line1: str) -> Optional[int]:
    """NORAD catalog number from TLE line 1 (columns 3-7)."""
    line1 = (line1 or "").strip()
    if len(line1) < 7:
        return None
    try:
        return int(line1[2:7])
    except ValueError:
        return None


def parse_intl_designator(line1: str) -> Optional[str]:
    """International designator from TLE line 1 (columns 12-17), e.g. 98067A."""
    line1 = (line1 or "").strip()
    if len(line1) < 17:
        return None
    designator = line1[11:17].strip()
    return designator or None


def parse_tle_epoch_utc(line1: str) -> Optional[str]:
    """Element-set epoch from TLE line 1 as ISO-8601 UTC."""
    line1 = (line1 or "").strip()
    if len(line1) < 32:
        return None
    try:
        epoch_field = line1[18:32].strip()
        yy = int(epoch_field[:2])
        day_of_year = float(epoch_field[2:])
        year = 2000 + yy if yy < 57 else 1900 + yy
        epoch_dt = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1.0)
        return epoch_dt.isoformat()
    except (ValueError, IndexError):
        return None


def approximate_launch_date(line1: str) -> str:
    """Approximate launch year from international designator (not exact launch date)."""
    designator = parse_intl_designator(line1)
    if not designator or len(designator) < 2:
        return "Unknown"
    try:
        yy = int(designator[:2])
        year = 2000 + yy if yy < 57 else 1900 + yy
        launch_seq = designator[2:5].lstrip("0") or "0"
        return f"~{year} (catalog seq. {launch_seq})"
    except ValueError:
        return "Unknown"


def get_satellite_metadata(name: str, line1: str, line2: str) -> Dict[str, Any]:
    """Catalog metadata derived from TLE (operator/decay need external SATCAT for full accuracy)."""
    norad = parse_norad_id(line1)
    designator = parse_intl_designator(line1)
    operator = get_satellite_country(name)
    return {
        "norad_id": norad,
        "object_id": designator,
        "launch_date": approximate_launch_date(line1),
        "operator": operator,
        "decay_date": "Active (in catalog)",
        "tle_epoch": parse_tle_epoch_utc(line1),
    }


def get_satellite_country(sat_name: str) -> str:
    """
    Maps satellite name to country/organization using keyword matching.
    Falls back to 'Unknown' if not found.
    """
    if not sat_name:
        return 'Unknown'
    
    sat_upper = sat_name.upper()
    
    # Direct keyword matching from mapping dictionary
    for key, country in SATELLITE_COUNTRY_MAP.items():
        if key in sat_upper:
            return country
    
    # Additional patterns for unmatched satellites
    if any(x in sat_upper for x in ['COSMOS', 'ZENIT', 'PROTON']):
        return 'Russia'
    elif any(x in sat_upper for x in ['SOYUZ', 'PROGRESS']):
        return 'Russia'
    elif any(x in sat_upper for x in ['TIANGONG', 'SHENZHOU', 'CHANG']):
        return 'China'
    elif any(x in sat_upper for x in ['RESSURS', 'MOLNIYA']):
        return 'Russia'
    elif any(x in sat_upper for x in ['AÉSAT', 'HELIOS']):
        return 'France'
    elif any(x in sat_upper for x in ['COPERNICUS', 'SENTINEL']):
        return 'EU'
    elif any(x in sat_upper for x in ['CARTOSAT', 'ASTROSAT']):
        return 'India'
    elif any(x in sat_upper for x in ['JERS', 'AKARI', 'HAYABUSA']):
        return 'Japan'
    elif any(x in sat_upper for x in ['RASCOM', 'NILESAT']):
        return 'Africa'
    else:
        # Default to USA for common debris/sats without clear ownership
        return 'Other'

def calculate_orbit_state(line1: str, line2: str, dt: Optional[datetime] = None) -> OrbitState:
    """
    Calculates the satellite's geodetic state (lat, lon, alt, speed) at a given datetime.
    
    If dt is None, uses the current UTC time.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        # If naive datetime is provided, assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
        
    # Standardize time to UTC
    dt_utc = dt.astimezone(timezone.utc)
    
    # Get Julian Date components from sgp4
    jd, fr = jday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour, dt_utc.minute,
        dt_utc.second + dt_utc.microsecond / 1e6
    )
    
    # Initialize Satrec object
    try:
        satellite = Satrec.twoline2rv(line1, line2)
    except Exception as e:
        logger.error(f"Error parsing TLE lines with SGP4: {e}")
        raise ValueError(f"Invalid TLE format: {e}")
        
    # Propagate orbit using SGP4
    error, position, velocity = satellite.sgp4(jd, fr)
    
    if error != 0:
        err_msg = SGP4_ERRORS.get(error, "Unknown SGP4 error")
        logger.error(f"SGP4 Propagation Error {error}: {err_msg}")
        raise ValueError(f"SGP4 propagation failed: {err_msg} (code {error})")
        
    # SGP4 returns position in km, and velocity in km/s in the TEME frame
    pos_x, pos_y, pos_z = position
    vel_x, vel_y, vel_z = velocity
    
    # Convert TEME to Geodetic LLA
    lat, lon, alt = teme_to_lla(pos_x, pos_y, pos_z, jd, fr)
    
    # Calculate speed as magnitude of velocity vector
    speed = math.sqrt(vel_x**2 + vel_y**2 + vel_z**2)
    
    return OrbitState(
        latitude=lat,
        longitude=lon,
        altitude_km=alt,
        speed_kms=speed,
        timestamp=dt_utc.isoformat()
    )

if __name__ == "__main__":
    import json
    
    print("Self-Testing Orbit Calculator with ISS TLE...")
    
    # Standard ISS TLE
    iss_line1 = "1 25544U 98067A   20351.58782928  .00001099  00000-0  27827-4 0  9997"
    iss_line2 = "2 25544  51.6441  21.2829 0001683  84.5822 355.2031 15.49163278260761"
    
    try:
        # 1. Test current time
        state = calculate_orbit_state(iss_line1, iss_line2)
        print("\nCalculated State (Current Time):")
        print(json.dumps(state.to_dict(), indent=2))
        
        # 2. Test historical epoch (to match known reference coordinates)
        historical_dt = datetime(2020, 12, 16, 14, 6, 0, tzinfo=timezone.utc)
        historical_state = calculate_orbit_state(iss_line1, iss_line2, historical_dt)
        print(f"\nCalculated State (Historical Epoch: {historical_dt}):")
        print(json.dumps(historical_state.to_dict(), indent=2))
        
    except Exception as e:
        print(f"Error during calculation: {e}")
