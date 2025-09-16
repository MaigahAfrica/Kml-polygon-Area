
"""
kml_area.py
-----------
Utilities to parse KML Polygon placemarks and compute areas (in hectares)
and approximate centroid (lat, lon). No third-party deps.
"""

from xml.etree import ElementTree as ET
from typing import List, Tuple, Dict, Optional
import math
import os
import csv

# Earth radius (meters)
EARTH_RADIUS = 6371008.8  # IUGG mean Earth radius

# KML namespace handling
KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}

def _unwrap_lons(lons: List[float]) -> List[float]:
    """Unwrap longitudes to avoid large jumps across the dateline for area calc."""
    unwrapped = [lons[0]]
    for i in range(1, len(lons)):
        d = lons[i] - lons[i-1]
        if d > 180:
            unwrapped.append(unwrapped[-1] + (d - 360))
        elif d < -180:
            unwrapped.append(unwrapped[-1] + (d + 360))
        else:
            unwrapped.append(unwrapped[-1] + d)
    # Convert back to absolute longitudes relative to the first
    base = lons[0]
    result = [base + (u - unwrapped[0]) for u in unwrapped]
    return result

def spherical_polygon_area_sq_m(lats_deg: List[float], lons_deg: List[float]) -> float:
    """
    Approximate area of a (small) spherical polygon on Earth using
    the l'Huilier/Chamberlain-Duquette style formula.
    Vertices must be ordered and the polygon closed (first==last). If not closed,
    the function will close it.
    Returns area in square meters.
    """
    if len(lats_deg) < 3:
        return 0.0
    # Ensure closed polygon
    if lats_deg[0] != lats_deg[-1] or lons_deg[0] != lons_deg[-1]:
        lats_deg = lats_deg + [lats_deg[0]]
        lons_deg = lons_deg + [lons_deg[0]]

    # Unwrap longitudes to avoid jumps
    lons_deg = _unwrap_lons(lons_deg)

    lats = [math.radians(lat) for lat in lats_deg]
    lons = [math.radians(lon) for lon in lons_deg]

    # Spherical excess approximation
    # Area on unit sphere ≈ 0.5 * sum( (lon_{i+1} - lon_i) * (sin(lat_{i+1}) + sin(lat_i)) )
    # Then multiply by R^2 for square meters. Take absolute value.
    total = 0.0
    for i in range(len(lats) - 1):
        lon1, lon2 = lons[i], lons[i+1]
        lat1, lat2 = lats[i], lats[i+1]
        total += (lon2 - lon1) * (math.sin(lat1) + math.sin(lat2))
    area_on_unit_sphere = 0.5 * abs(total)
    area_sq_m = area_on_unit_sphere * (EARTH_RADIUS ** 2)
    return area_sq_m

def centroid_latlon(lats_deg: List[float], lons_deg: List[float]) -> Tuple[float, float]:
    """
    Approximate centroid by averaging 3D Cartesian coordinates on the unit sphere,
    then converting back to lat/lon.
    """
    if not lats_deg:
        return (0.0, 0.0)

    x = y = z = 0.0
    for lat_deg, lon_deg in zip(lats_deg, lons_deg):
        lat = math.radians(lat_deg)
        lon = math.radians(lon_deg)
        x += math.cos(lat) * math.cos(lon)
        y += math.cos(lat) * math.sin(lon)
        z += math.sin(lat)
    n = len(lats_deg)
    x /= n
    y /= n
    z /= n
    hyp = math.hypot(x, y)
    lat = math.degrees(math.atan2(z, hyp))
    lon = math.degrees(math.atan2(y, x))
    return (lat, lon)

def parse_kml_polygons(kml_path: str) -> List[Dict]:
    """
    Parse KML file and return a list of dicts with keys:
      - id: Placemark name or id
      - coords: list of (lat, lon) tuples for outer boundary
    Only handles <Polygon> with <outerBoundaryIs>.
    """
    results = []
    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
    except ET.ParseError:
        return results  # skip bad file

    # Find all Placemark elements
    for pm in root.findall(".//kml:Placemark", namespaces=KML_NS):
        # Find name
        name_el = pm.find("kml:name", namespaces=KML_NS)
        pid = name_el.text.strip() if (name_el is not None and name_el.text) else os.path.basename(kml_path)

        # Find polygon outer boundary
        coords_el = pm.find(".//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", namespaces=KML_NS)
        if coords_el is None or not coords_el.text:
            continue

        # KML coordinates are "lon,lat[,alt]" separated by spaces (and/or newlines)
        raw = coords_el.text.strip()
        parts = [p for p in raw.replace("\n", " ").split(" ") if p]
        lats, lons = [], []
        for p in parts:
            try:
                lon_str, lat_str, *_ = p.split(",")
                lon = float(lon_str)
                lat = float(lat_str)
                lats.append(lat)
                lons.append(lon)
            except Exception:
                continue

        if len(lats) >= 3:
            results.append({"id": pid, "lats": lats, "lons": lons})
    return results

def summarize_kml_folder(folder: str) -> List[Dict]:
    """
    Walk a folder, parse all .kml files, compute area (ha) and centroid for each polygon.
    Returns a list of rows: {"Plot_ID","Area_ha","Latitude","Longitude","Source_File"}
    """
    rows = []
    for root, _, files in os.walk(folder):
        for fname in files:
            if not fname.lower().endswith(".kml"):
                continue
            fpath = os.path.join(root, fname)
            polygons = parse_kml_polygons(fpath)
            for poly in polygons:
                area_m2 = spherical_polygon_area_sq_m(poly["lats"], poly["lons"])
                area_ha = area_m2 / 10000.0
                lat_c, lon_c = centroid_latlon(poly["lats"], poly["lons"])
                rows.append({
                    "Plot_ID": poly["id"],
                    "Area_ha": round(area_ha, 4),
                    "Latitude": round(lat_c, 6),
                    "Longitude": round(lon_c, 6),
                    "Source_File": os.path.relpath(fpath, folder)
                })
    return rows

def write_csv(rows: List[Dict], out_csv: str) -> None:
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Plot_ID","Area_ha","Latitude","Longitude","Source_File"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
