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

    # 🔹 Show all rows instead of only top 5
    st.subheader("Preview of Uploaded Data (All Rows)")
    st.dataframe(df)

    # --- User Input ---
    lat_col = st.selectbox("Select **Latitude** column", df.columns)
    lon_col = st.selectbox("Select **Longitude** column", df.columns)

    # 🔹 CRS Selection (New Section)
    st.subheader("Select Coordinate Reference System (CRS)")
    crs_options = {
        "4326 - WGS 84": "4326",
        "3380 - GDM2000 / MRSO": "3380",
        "3376 - GDM2000 / BRSO": "3376",
        "Other (custom EPSG code)": "custom"
    }

    selected_crs_label = st.selectbox("Choose CRS:", list(crs_options.keys()))
    selected_crs = crs_options[selected_crs_label]

    if selected_crs == "custom":
        custom_epsg = st.text_input("Enter your custom EPSG code:", "")
        crs_input = custom_epsg.strip() if custom_epsg else "4326"
    else:
        crs_input = selected_crs

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
