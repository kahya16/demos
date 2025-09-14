# -*- coding: utf-8 -*-
import streamlit as st
import folium
from folium.plugins import MousePosition
import geopandas as gpd
import rasterio
from streamlit_folium import folium_static
from urllib.parse import quote

st.set_page_config(page_title="Emiray DEMOS", page_icon="🗺️", layout="wide")

# Hide Streamlit chrome
st.markdown(
    """
    <style>
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; }
    button[title="View fullscreen"]{ visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Georeferencing Demo")

# Center of map
center = [41.0165, 28.9492]

# Base map
m = folium.Map(location=center, zoom_start=13, control_scale=True, tiles=None, width='100%')
folium.TileLayer('OpenStreetMap', name='OpenStreetMap', control=True).add_to(m)

# Data
gdf = gpd.read_file("point.geojson")

def _type_style(type_str: str):
    t = (type_str or "").lower()
    # Defaults
    icon, color = "star", "blue"
    badge_bg, badge_text = "#2563eb", "P"
    if "rampart" in t:
        icon, color = "shield", "darkred"
        badge_bg, badge_text = "#b91c1c", "R"
    elif "gate" in t:
        icon, color = "bookmark", "red"
        badge_bg, badge_text = "#ef4444", "G"
    elif "tower" in t:
        icon, color = "flag", "orange"
        badge_bg, badge_text = "#f97316", "T"
    elif "church" in t:
        icon, color = "university", "green"
        badge_bg, badge_text = "#16a34a", "C"
    elif "monast" in t:
        icon, color = "university", "green"
        badge_bg, badge_text = "#16a34a", "M"
    elif t in ("poi", "point"):
        icon, color = "star", "blue"
        badge_bg, badge_text = "#2563eb", "P"
    return icon, color, badge_bg, badge_text

def popup_html(title: str, type_str: str, lat: float = None, lon: float = None) -> str:
    url = f"https://www.google.com/search?q={quote(title)}"
    sv_url = (
        f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
        if lat is not None and lon is not None else "#"
    )
    icon, color, badge_bg, badge_text = _type_style(type_str)
    return f"""
    <div style='font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; width:260px;'>
      <div style='border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,.12);overflow:hidden;border:1px solid #eef0f3;background:#fff;'>
        <div style='padding:14px 16px 10px;background:linear-gradient(180deg,#fff 0%, #f7f9fb 100%);border-bottom:1px solid #eef0f3;'>
          <div style='display:flex;align-items:center;gap:10px;'>
            <span style='display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:6px;background:{badge_bg};color:#fff;font-weight:700;font-size:12px;'>{badge_text}</span>
            <div style='font-size:16px;font-weight:700;color:#111827;line-height:1.3;'>{title}</div>
          </div>
          <div style='font-size:12px;color:#6b7280;margin-top:6px;'>Type: {type_str or 'Unknown'}</div>
        </div>
        <div style='padding:14px 16px; display:flex; gap:8px; flex-wrap: wrap;'>
          <a href='{url}' target='_blank' rel='noopener' style='display:inline-flex;align-items:center;gap:8px;text-decoration:none;background:#16a34a;color:#fff;border-radius:8px;padding:8px 12px;font-weight:600;font-size:13px;'>
            <span style='display:inline-block;width:16px;height:16px;border-radius:2px;background:#fff;color:#16a34a;text-align:center;line-height:16px;font-weight:700;'>G</span>
            Google'da Ara
          </a>
          <a href='{sv_url}' target='_blank' rel='noopener' style='display:inline-flex;align-items:center;gap:8px;text-decoration:none;background:#2563eb;color:#fff;border-radius:8px;padding:8px 12px;font-weight:600;font-size:13px;'>
            <span style='display:inline-block;width:16px;height:16px;border-radius:2px;background:#fff;color:#2563eb;text-align:center;line-height:16px;font-weight:700;'>SV</span>
            Street View
          </a>
        </div>
      </div>
    </div>
    """

@st.cache_data(show_spinner=False)
def load_raster(path: str, max_size: int = 1800):
    import numpy as np
    from PIL import Image
    with rasterio.open(path) as src:
        arr = src.read(1)
        bounds = src.bounds
    # Normalize -> 8-bit
    a_min, a_max = float(arr.min()), float(arr.max())
    if a_max > a_min:
        arr8 = ((arr - a_min) / (a_max - a_min) * 255.0).astype('uint8')
    else:
        arr8 = arr.astype('uint8')
    # Downscale for browser
    h, w = arr8.shape
    scale = max(h, w) / max_size if max(h, w) > max_size else 1.0
    if scale > 1.0:
        new_w, new_h = int(w / scale), int(h / scale)
        img = Image.fromarray(arr8)
        img = img.resize((new_w, new_h), Image.BILINEAR)
        arr8 = np.array(img)
    return arr8, bounds

# Always add georeferenced raster (cached)
try:
    band, bounds = load_raster("Byzantine_Constantinople-en_modified.tif")
    from folium import raster_layers
    raster_layers.ImageOverlay(
        image=band,
        bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        opacity=0.6,
        name="Georeferenced Image",
    ).add_to(m)
except Exception as e:
    st.warning(f"Raster yüklenemedi: {e}")

MousePosition().add_to(m)

# Points as Marker with type-based icons and styled popups
gdf = gdf.copy()
if "name" not in gdf.columns:
    gdf["name"] = "Location"
if "type" not in gdf.columns:
    gdf["type"] = "PoI"
points_fg = folium.FeatureGroup(name="Points", show=True)
for row in gdf.itertuples():
    geom = getattr(row, 'geometry', None)
    if geom and geom.geom_type == 'Point':
        lat, lon = geom.y, geom.x
        title = str(getattr(row, 'name', 'Location'))
        t = str(getattr(row, 'type', 'PoI'))
        icon_name, color, _, _ = _type_style(t)
        # Font Awesome prefix for richer icons
        icon = folium.Icon(color=color, icon=icon_name, prefix='fa')
        folium.Marker(
            location=[lat, lon],
            icon=icon,
            tooltip=f"{title} ({t})",
            popup=folium.Popup(popup_html(title, t, lat, lon), max_width=320),
        ).add_to(points_fg)
points_fg.add_to(m)

folium.LayerControl().add_to(m)

# Make container full-width and map tall
st.markdown(
    """
    <style>
      .block-container { padding-top: 0rem; padding-bottom: 0rem; max-width: 100% !important; }
      .st-emotion-cache-1jicfl2 { padding: 0 !important; } /* fallback */
    </style>
    """,
    unsafe_allow_html=True,
)

# Render static map to avoid reruns on zoom/pan
folium_static(m, width= 1300, height=500)
