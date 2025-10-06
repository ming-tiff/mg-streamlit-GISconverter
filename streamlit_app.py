import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import zipfile
import io
import os

st.set_page_config(page_title="CSV to Shapefile Converter", page_icon="🌍", layout="wide")

st.title("🌍 CSV to Shapefile Converter")
st.markdown("Easily convert your CSV data into a shapefile using this tool.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    # Let user choose which columns are lat/lon
    lat_col = st.selectbox("Select Latitude column", df.columns)
    lon_col = st.selectbox("Select Longitude column", df.columns)

    # CRS input
    crs_input = st.text_input("Enter CRS (EPSG code, e.g., 4326 for WGS84)", "4326")

    if st.button("Convert to Shapefile"):
    try:
        # Create geometry column
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
            crs=f"EPSG:{crs_input}"
        )

        # Derive output name from uploaded CSV
        base_name = os.path.splitext(uploaded_file.name)[0]

        # Save shapefile to memory (as ZIP)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            temp_dir = "temp_shp"
            os.makedirs(temp_dir, exist_ok=True)

            # 👉 NEW: use CSV name for shapefile
            shp_path = os.path.join(temp_dir, f"{base_name}.shp")
            gdf.to_file(shp_path)

            # Add all shapefile parts
            for filename in os.listdir(temp_dir):
                zf.write(os.path.join(temp_dir, filename), arcname=filename)

        st.success("✅ Conversion successful! Click below to download the shapefile.")

        # 👉 NEW: use CSV name for ZIP download
        st.download_button(
            label="📥 Download Shapefile (ZIP)",
            data=buffer.getvalue(),
            file_name=f"{base_name}.zip",
            mime="application/zip"
        )

        # Clean up
        for f in os.listdir("temp_shp"):
            os.remove(os.path.join("temp_shp", f))
        os.rmdir("temp_shp")

    except Exception as e:
        st.error(f"❌ Error: {e}"
