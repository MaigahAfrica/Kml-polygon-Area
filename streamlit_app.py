
"""
streamlit_app.py
----------------
A tiny Streamlit UI to compute polygon areas from uploaded KML folder (zipped).
Run with:
    streamlit run streamlit_app.py
"""
import streamlit as st
import zipfile, io, os, tempfile
from kml_area import summarize_kml_folder, write_csv

st.title("KML Polygon Area Calculator")
st.write("Upload a ZIP of your KML folder. We'll compute area (ha) and centroid for each polygon.")

uploaded = st.file_uploader("Upload KML folder as .zip", type=["zip"])

if uploaded is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = os.path.join(tmpdir, "in.zip")
        with open(zpath, "wb") as f:
            f.write(uploaded.read())
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(os.path.join(tmpdir, "unzipped"))
        rows = summarize_kml_folder(os.path.join(tmpdir, "unzipped"))
        out_csv = os.path.join(tmpdir, "results.csv")
        write_csv(rows, out_csv)
        st.success(f"Processed {len(rows)} polygons.")
        with open(out_csv, "rb") as f:
            st.download_button("Download results CSV", f, file_name="kml_areas.csv")
