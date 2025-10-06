import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import zipfile
import io
import os
import folium
from streamlit_folium import st_folium

# --- Streamlit Page Config ---
st.set_page_config(page_title="CSV to Shapefile Converter", page_icon="🌍", layout="wide")

st.title("🌍 CSV to Shapefile Converter")
st.markdown("Easily convert your CSV data into a Shapefile. Upload a CSV file with Latitude and Longitude columns.")

# --- Upload CSV ---
uploaded_file = st.file_uploader("📤 Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Read CSV
    df = pd.read_csv(uploaded_file)

    # 🔹 Show all rows
    st.subheader("📋 Preview of Uploaded Data (All Rows)")
    st.dataframe(df, use_container_width=True)

    # --- User Input ---
    lat_col = st.selectbox("Select **Latitude** column", df.columns)
    lon_col = st.selectbox("Select **Longitude** column", df.columns)

    # --- CRS Selection ---
    st.subheader("🌐 Select Coordinate Reference System (CRS)")
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

    # --- Folium Map Preview ---
    st.subheader("🗺️ Interactive Map Preview")
    try:
        # Prepare data for mapping
        preview_df = df[[lat_col, lon_col]].dropna()
        if not preview_df.empty:
            # Center map around mean coordinates
            center_lat = preview_df[lat_col].mean()
            center_lon = preview_df[lon_col].mean()

            # Create Folium map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap")

            # Add points
            for _, row in preview_df.iterrows():
                folium.CircleMarker(
                    location=[row[lat_col], row[lon_col]],
                    radius=5,
                    color="blue",
                    fill=True,
                    fill_color="cyan",
                    fill_opacity=0.7,
                    tooltip=f"Lat: {row[lat_col]}, Lon: {row[lon_col]}"
                ).add_to(m)

            # Render Folium map in Streamlit
            st_folium(m, width=800, height=500)
        else:
            st.warning("⚠️ No valid coordinates found for preview.")
    except Exception as e:
        st.warning(f"⚠️ Unable to display map preview: {e}")

    # --- Convert Button ---
    if st.button("Convert to Shapefile"):
        try:
            # Create GeoDataFrame
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs=f"EPSG:{crs_input}"
            )

            # Derive base name from uploaded CSV
            base_name = os.path.splitext(uploaded_file.name)[0]

            # Define temp folder
            temp_dir = "temp_shp"

            # Clean up old temp folder
            if os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)

            # Create fresh folder
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
