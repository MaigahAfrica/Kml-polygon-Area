

"""
app.py
------
CLI to compute areas from a folder of KML polygon files.

Usage:
    python app.py --in /path/to/kml_folder --out /path/to/output.csv
"""
import argparse, os, sys
from kml_area import summarize_kml_folder, write_csv

def main():
    ap = argparse.ArgumentParser(description="Compute polygon areas (ha) and centroids from KML files.")
    ap.add_argument("--in", dest="in_folder", required=True, help="Input folder containing .kml files")
    ap.add_argument("--out", dest="out_csv", required=True, help="Output CSV path")
    args = ap.parse_args()

    if not os.path.isdir(args.in_folder):
        print(f"Input folder not found: {args.in_folder}", file=sys.stderr)
        sys.exit(1)

    rows = summarize_kml_folder(args.in_folder)
    if not rows:
        print("No polygons found in KML files.", file=sys.stderr)
    write_csv(rows, args.out_csv)
    print(f"Done. Wrote {len(rows)} rows to {args.out_csv}")

if __name__ == "__main__":
    main()
