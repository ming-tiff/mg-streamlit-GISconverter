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
st.markdown("Easily convert your CSV data into Shapefile(s). Upload one or more CSV files with Latitude and Longitude columns.")

# --- Upload CSV (multiple) ---
uploaded_files = st.file_uploader("📤 Upload one or more CSV files", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    # --- CRS Selection (shared for all files) ---
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

    # Prepare for zipping all shapefiles
    temp_dir = "temp_shp_multi"
    os.makedirs(temp_dir, exist_ok=True)

    all_gdfs = []  # to store GeoDataFrames for later zipping

    for uploaded_file in uploaded_files:
        st.divider()
        st.subheader(f"📁 File: {uploaded_file.name}")

        # Read CSV
        df = pd.read_csv(uploaded_file)

        # 🔹 Show all rows
        st.subheader("📋 Preview of Uploaded Data (All Rows)")
        st.dataframe(df, use_container_width=True)

        # --- User Input ---
        lat_col = st.selectbox(f"Select **Latitude** column for {uploaded_file.name}", df.columns, key=f"lat_{uploaded_file.name}")
        lon_col = st.selectbox(f"Select **Longitude** column for {uploaded_file.name}", df.columns, key=f"lon_{uploaded_file.name}")

        # --- Folium Map Preview ---
        st.subheader("🗺️ Interactive Map Preview")
        try:
            preview_df = df[[lat_col, lon_col]].dropna()
            if not preview_df.empty:
                center_lat = preview_df[lat_col].mean()
                center_lon = preview_df[lon_col].mean()
                m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap")
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
                st_folium(m, width=800, height=500, key=f"map_{uploaded_file.name}")
            else:
                st.warning("⚠️ No valid coordinates found for preview.")
        except Exception as e:
            st.warning(f"⚠️ Unable to display map preview: {e}")

        # Convert immediately (collect all for one zip)
        try:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs=f"EPSG:{crs_input}"
            )

            base_name = os.path.splitext(uploaded_file.name)[0]
            shp_path = os.path.join(temp_dir, f"{base_name}.shp")
            gdf.to_file(shp_path)
            all_gdfs.append(base_name)

            st.success(f"✅ {base_name}.shp created successfully!")
        except Exception as e:
            st.error(f"❌ Error converting {uploaded_file.name}: {e}")

    # --- Combine all shapefiles into single ZIP ---
    if all_gdfs and st.button("📦 Download All Shapefiles as ZIP"):
        try:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zf:
                for base_name in all_gdfs:
                    shp_parts = [f for f in os.listdir(temp_dir) if f.startswith(base_name)]
                    for filename in shp_parts:
                        file_path = os.path.join(temp_dir, filename)
                        zf.write(file_path, arcname=filename)

            st.success(f"✅ {len(all_gdfs)} shapefile(s) ready for download!")
            st.download_button(
                label="📥 Download All Shapefiles (ZIP)",
                data=buffer.getvalue(),
                file_name="converted_shapefiles.zip",
                mime="application/zip"
            )

            # Cleanup after zipping
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

        except Exception as e:
            st.error(f"❌ Error creating ZIP: {e}")

else:
    st.info("👆 Please upload one or more CSV files to begin.")


#this is original code, dont change any except that what i want to improve
#make the map with the point have the label depends on what i command to label apear, either it Asset ID or Either the type or else
