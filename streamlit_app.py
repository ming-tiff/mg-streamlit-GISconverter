import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import zipfile
import io
import os

# --- Streamlit Page Config ---
st.set_page_config(page_title="CSV to Shapefile Converter", page_icon="🌍", layout="wide")

st.title("🌍 CSV to Shapefile Converter")
st.markdown("Easily convert your CSV data into a Shapefile. Upload a CSV file with Latitude and Longitude columns.")

# --- Upload CSV ---
uploaded_file = st.file_uploader("📤 Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Read CSV
    df = pd.read_csv(uploaded_file)
    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    # --- User Input ---
    lat_col = st.selectbox("Select **Latitude** column", df.columns)
    lon_col = st.selectbox("Select **Longitude** column", df.columns)
    crs_input = st.text_input("Enter CRS (EPSG code, e.g., 4326 for WGS84)", "4326")

    # --- Convert Button ---
    if st.button("Convert to Shapefile"):
        try:
            # Create GeoDataFrame
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs=f"EPSG:{crs_input}"
            )

            # Derive base name from uploaded CSV file
            base_name = os.path.splitext(uploaded_file.name)[0]

            # Define temp folder
            temp_dir = "temp_shp"

            # Clean old temp folder (if exists)
            if os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)

            # Create fresh temp folder
            os.makedirs(temp_dir, exist_ok=True)

            # Save shapefile
            shp_path = os.path.join(temp_dir, f"{base_name}.shp")
            gdf.to_file(shp_path)

            # Ensure shapefile parts exist
            shp_parts = [f for f in os.listdir(temp_dir) if f.startswith(base_name)]
            if not shp_parts:
                raise FileNotFoundError("Shapefile components were not created correctly.")

            # Create ZIP in memory
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zf:
                for filename in shp_parts:
                    file_path = os.path.join(temp_dir, filename)
                    zf.write(file_path, arcname=filename)

            st.success(f"✅ {base_name}.zip is ready for download!")

            # Download button
            st.download_button(
                label="📥 Download Shapefile (ZIP)",
                data=buffer.getvalue(),
                file_name=f"{base_name}.zip",
                mime="application/zip"
            )

            # Cleanup after zipping
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

        except Exception as e:
            st.error(f"❌ Error: {e}")

else:
    st.info("👆 Please upload a CSV file to begin.")
