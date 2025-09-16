
# KML Polygon Area App

This simple, offline Python app scans a folder of `.kml` files, extracts polygon Placemarks, and outputs their **area (hectares)** and **centroid GPS coordinates**.

**Example output columns:**
```
Plot_ID,Area_ha,Latitude,Longitude,Source_File
P007-P02,0.29,6.001024,-2.330695,blocks/p007.kml
```

## Quick Start (CLI)

1. Ensure you have Python 3.8+ installed.
2. Unzip this project.
3. Run:
   ```bash
   python app.py --in /path/to/your/kml_folder --out /path/to/save/results.csv
   ```

The script uses a spherical Earth approximation (no external libraries). For typical farm-sized polygons, the error is generally small (within a few percent).

## Streamlit mini-app

If you prefer a UI and have Streamlit installed:

```bash
pip install streamlit
streamlit run streamlit_app.py
```

Then upload a **ZIP of your KML folder** to get a downloadable CSV.

## Notes & Assumptions

- Parses `<Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>` only.
- Uses the Placemark `<name>` as `Plot_ID`. If absent, falls back to filename.
- Coordinates are expected in KML order: `lon,lat[,alt]`.
- Area computed with a standard spherical polygon formula; result reported in **hectares**.
- Centroid is an approximate geographic centroid (unit-sphere mean).

## Output Fields

- `Plot_ID`: From KML Placemark name (or source file).
- `Area_ha`: Area in hectares (rounded to 4 decimals).
- `Latitude`, `Longitude`: Approximate centroid of the polygon.
- `Source_File`: Path of the source `.kml` file relative to the input folder.

## Troubleshooting

- If no rows are produced, confirm your KMLs contain Polygon placemarks and outer boundaries.
- Very complex/multi-geometry KMLs may need customization.
- For extremely accurate areas, consider projecting to an equal-area CRS per region or using a geodesic library.
