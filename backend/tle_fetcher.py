import urllib.request
import urllib.error
import os
import time
from typing import List
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── URLs ──────────────────────────────────────────────────────────────────────
CELESTRAK_URL    = "https://celestrak.org/pub/TLE/catalog.txt"
FALLBACK_URL     = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
AMSAT_MIRROR_URL = "https://www.amsat.org/amsat/ftp/keps/current/nasabare.txt"

# ── Cache ─────────────────────────────────────────────────────────────────────
CACHE_FILE          = os.path.join(os.path.dirname(__file__), "tle_cache.txt")
CACHE_DURATION_SECS = 2 * 60 * 60   # refresh after 2 hours
MIN_HEALTHY_OBJECTS = 100            # minimum objects to consider cache valid


def _count_tle_objects(content: str) -> int:
    """Count how many valid 3-line TLE blocks are in a raw TLE string."""
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    count = 0
    for i in range(0, len(lines) - 2, 3):
        if lines[i + 1].startswith('1 ') and lines[i + 2].startswith('2 '):
            count += 1
    return count


def _read_cache() -> str | None:
    """Return cache file contents, or None if it doesn't exist / can't be read."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read cache file: {e}")
    return None


def _write_cache(content: str, new_count: int) -> None:
    """
    Write content to cache ONLY if it contains more objects than what's
    already cached — this prevents a 96-satellite AMSAT fetch from silently
    downgrading a 15,503-satellite cache.
    """
    existing = _read_cache()
    if existing:
        current_count = _count_tle_objects(existing)
        if new_count < current_count:
            logger.info(
                f"Skipping cache write: new data has {new_count} objects "
                f"vs existing {current_count}. Keeping larger cache."
            )
            return

    try:
        os.makedirs(os.path.dirname(CACHE_FILE) or '.', exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Cache updated: {new_count} objects → {CACHE_FILE}")
    except Exception as e:
        logger.warning(f"Could not write cache: {e}")


def verify_and_clean_cache() -> None:
    """
    On startup: if the cache exists but has fewer than MIN_HEALTHY_OBJECTS,
    delete it so a fresh fetch is forced.  A healthy cache is left untouched.
    """
    content = _read_cache()
    if content is None:
        logger.info("No local cache found — will fetch live on first call.")
        return

    num = _count_tle_objects(content)
    if num < MIN_HEALTHY_OBJECTS:
        logger.warning(
            f"Cache has only {num} objects (< {MIN_HEALTHY_OBJECTS}). "
            f"Deleting to force fresh fetch..."
        )
        try:
            os.remove(CACHE_FILE)
        except Exception as e:
            logger.warning(f"Could not remove cache: {e}")
    else:
        logger.info(f"Cache healthy: {num} objects in {CACHE_FILE}")


# Run immediately when this module is imported (i.e. on Flask startup)
verify_and_clean_cache()


@dataclass
class TLEData:
    name:  str
    line1: str
    line2: str

    def to_dict(self) -> dict:
        return {"name": self.name, "line1": self.line1, "line2": self.line2}


def fetch_tle_data(url: str = CELESTRAK_URL) -> str:
    """
    Smart fetch strategy:

    1. If a HEALTHY cache (≥ MIN_HEALTHY_OBJECTS) exists and is FRESH (< 2 h),
       return it immediately — no network call.
    2. If the cache is healthy but STALE, attempt a live fetch.
       On success, update the cache only if the new data is larger.
       On failure, fall back to the stale (but large) cache.
    3. If the cache is missing/invalid, attempt a live fetch from the
       primary URL, then FALLBACK_URL, then AMSAT_MIRROR_URL in order.
    4. Last resort: return whatever is in the cache file, even if stale/small.
    """
    # ── Step 1 / 2: Evaluate existing cache ───────────────────────────────────
    cached_content = _read_cache()
    cache_healthy  = False
    cache_fresh    = False

    if cached_content:
        cached_count = _count_tle_objects(cached_content)
        cache_healthy = cached_count >= MIN_HEALTHY_OBJECTS
        if cache_healthy:
            age = time.time() - os.path.getmtime(CACHE_FILE)
            cache_fresh = age < CACHE_DURATION_SECS
            if cache_fresh:
                logger.info(
                    f"Using fresh healthy cache: {cached_count} objects "
                    f"(age {int(age / 60)} min)"
                )
                return cached_content
            else:
                logger.info(
                    f"Cache stale ({int(age / 60)} min old, {cached_count} objects). "
                    f"Attempting live refresh..."
                )

    # ── Step 3: Live fetch ────────────────────────────────────────────────────
    urls_to_try = [url, FALLBACK_URL, AMSAT_MIRROR_URL]
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    }

    for target_url in urls_to_try:
        logger.info(f"Attempting live fetch from: {target_url}")
        try:
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8')

            # Reject CSV/metadata responses (Celestrak sometimes returns these)
            if "OBJECT_NAME" in content or "NORAD_CAT_ID" in content:
                logger.warning(f"{target_url} returned CSV — skipping.")
                continue

            new_count = _count_tle_objects(content)
            logger.info(f"Fetched {new_count} objects from {target_url}")
            _write_cache(content, new_count)

            # If the live fetch returned fewer objects than our cache, use cache
            if cache_healthy and cached_content:
                cached_count = _count_tle_objects(cached_content)
                if new_count < cached_count:
                    logger.info(
                        f"Live data ({new_count}) < cache ({cached_count}). "
                        f"Serving from cache."
                    )
                    return cached_content

            return content

        except Exception as e:
            logger.error(f"Failed to fetch from {target_url}: {e}")

    # ── Step 4: Last resort — return stale cache if any ───────────────────────
    if cached_content:
        logger.warning("All live fetches failed. Serving from existing cache.")
        return cached_content

    raise RuntimeError(
        "No TLE data available: all live sources failed and no local cache exists."
    )


def parse_tle_data(raw_data: str) -> List[TLEData]:
    """Parse raw 3-line TLE text into TLEData objects."""
    logger.info("Parsing TLE data...")
    lines    = [l.strip() for l in raw_data.splitlines() if l.strip()]
    tle_list = []

    for i in range(0, len(lines) - 2, 3):
        name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
        if line1.startswith('1 ') and line2.startswith('2 '):
            tle_list.append(TLEData(name=name, line1=line1, line2=line2))
        else:
            logger.warning(f"Skipping malformed block at line {i}: '{name}'")

    logger.info(f"Parsed {len(tle_list)} TLE objects.")
    return tle_list


def get_tles(url: str = CELESTRAK_URL) -> List[TLEData]:
    """Fetch and parse TLE data. Uses smart cache logic internally."""
    try:
        return parse_tle_data(fetch_tle_data(url))
    except Exception as e:
        logger.error(f"TLE pipeline failed: {e}")
        return []


if __name__ == "__main__":
    tles = get_tles()
    print(f"\nLoaded {len(tles)} TLEs.")
    for tle in tles[:3]:
        print(f"  {tle.name}")
