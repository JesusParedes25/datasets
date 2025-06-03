#!/usr/bin/env python
# coding: utf-8

# In[6]:


import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium

# URL RAW del archivo en GitHub
url = "https://raw.githubusercontent.com/JesusParedes25/datasets/main/tramites_ubicacion_pachuca_limpio%20(1).xls"

# Leer el CSV desde la URL
df = pd.read_csv(url)

# Preparamos listas únicas para los filtros
secretarias = ["Todos"] + sorted(df['secretaria.nombre'].dropna().unique().tolist())
dependencias = ["Todos"] + sorted(df['dependencia.nombre'].dropna().unique().tolist())
tramites = ["Todos"] + sorted(df['nombre'].dropna().unique().tolist())

# Sidebar con filtros
st.sidebar.title("Filtros")

secretaria_sel = st.sidebar.selectbox("Secretaría", secretarias)
dependencia_sel = st.sidebar.selectbox("Dependencia", dependencias)
tramite_sel = st.sidebar.selectbox("Trámite", tramites)

# Aplicar filtros
df_filtrado = df.copy()

if secretaria_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['secretaria.nombre'] == secretaria_sel]

if dependencia_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['dependencia.nombre'] == dependencia_sel]

if tramite_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['nombre'] == tramite_sel]

# Crear el mapa
pachuca_coords = [20.1011, -98.7591]
m = folium.Map(location=pachuca_coords, zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)

# Agregar los puntos filtrados
for _, row in df_filtrado.iterrows():
    try:
        lat = float(row['atencion.coordenada_y'])
        lon = float(row['atencion.coordenada_x'])
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px;">
            <b>Trámite:</b> {row['nombre']}<br>
            <b>Secretaría:</b> {row['secretaria.nombre']}<br>
            <b>Dependencia:</b> {row['dependencia.nombre']}<br>
            <b>Centro de atención:</b> {row['atencion.nombre']}<br>
            <b>Dirección:</b> {row['atencion.direccion']}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=400)
        ).add_to(marker_cluster)
    except:
        pass

# Mostrar el mapa dentro de Streamlit
st.title("Mapa Interactivo de Trámites en Pachuca")
st_folium(m, width=700, height=500)


# In[ ]:




