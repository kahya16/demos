# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 21:47:42 2024

@author: emiray
"""
import streamlit as st
st.set_page_config(
    page_title="Emiray DEMOS",
    page_icon="🌏",
    layout="wide",
)
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton { visibility:hidden;}
button[title="View fullscreen"]{
    visibility: hidden;}


</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


import folium
from folium.plugins import MousePosition
import geopandas as gpd
import rasterio
from streamlit_folium import folium_static
# Başlık
st.title("Georeferencing Demo")

# Fatih ilçesi koordinatlarını ayarlayalım
fatih_coords = [41.0165, 28.9492]
m = folium.Map(location=fatih_coords, zoom_start=13)
# Folium haritası oluşturalım
google_tiles = folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite Basemap'  # Katmana isim veriyoruz
).add_to(m)
# GeoJSON dosyasını yükleyelim
geojson_file = "point.geojson"  # Buraya kendi geojson dosyanızın yolunu ekleyin
gdf = gpd.read_file(geojson_file)

# GeoJSON katmanını haritaya ekleyelim
def style_function(feature):
    return {
        "fillOpacity": 0.4,
        "weight": 1,
        "color": "blue"
    }
with st.spinner('Loading points'):
    geojson_layer = folium.GeoJson(
        gdf,
        name="Point of Interest",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=["name"])  # İlgili alanlar seçilir
    ).add_to(m)
    
    # Kullanıcı tıkladığında bilgi alabilmesi için bir tıklama olayı ekleyelim
    def click_info(feature):
        properties = feature["properties"]
        info = f"Name: {properties.get('name', 'Bilinmiyor')}"
        st.write(info)

with st.spinner('Loading georeferenced raster'):
# TIFF dosyasını ekleyelim
    tiff_file = "Byzantine_Constantinople-en_modified.tif"  # Buraya kendi TIFF dosyanızın yolunu ekleyin
    with rasterio.open(tiff_file) as src:
        
        band = src.read(1)
        bounds = src.bounds
    
    # MousePosition plugin ile koordinat bilgisi ekleyelim
    MousePosition().add_to(m)
    
    # Haritayı Streamlit içerisinde gösterelim
    
    from folium import raster_layers
    # GeoJSON üzerine tıklama bilgisini yazdırma
    
    raster_layers.ImageOverlay(
            image=band,
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            opacity=0.7,
            name="Georeferenced Image"
        ).add_to(m)
    
        # Katman kontrolü ekle
    folium.LayerControl().add_to(m)
# Kullanıcı TIFF dosyasını yükleyebilir
with st.spinner('Loading map'):
    folium_static(m)