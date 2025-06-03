#!/usr/bin/env python
# coding: utf-8

# In[2]:


#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import json
from folium.plugins import MarkerCluster

# Configuración inicial de Streamlit
st.set_page_config(page_title="SIG de Trámites", layout="wide")
st.title("🗺️ Plataforma Interactiva de Trámites y Sucursales")

# ------------------- CACHE ---------------------

@st.cache_data
def cargar_csv(url_csv):
    return pd.read_csv(url_csv)

@st.cache_data
def procesar_datos(df_original):
    max_atencion = 85
    registros = []

    for _, row in df_original.iterrows():
        for i in range(max_atencion):
            direccion_col = f"atencion[{i}].direccion"
            coord_x_col = f"atencion[{i}].coordenadas.coordinates[0]"
            coord_y_col = f"atencion[{i}].coordenadas.coordinates[1]"

            if pd.notna(row.get(direccion_col)):
                registros.append({
                    "direccion": row[direccion_col],
                    "coordenada_x": row.get(coord_x_col),
                    "coordenada_y": row.get(coord_y_col),
                    "nombre": row["nombre"],
                    "secretaria": row["secretaria.nombre"],
                    "dependencia": row["dependencia.nombre"]
                })

    df_limpio = pd.DataFrame(registros)
    df_grouped = df_limpio.groupby(
        ['coordenada_x', 'coordenada_y', 'secretaria', 'dependencia']
    ).agg({
        'direccion': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
        'nombre': lambda x: list(set(x))
    }).reset_index()

    return df_grouped

@st.cache_data
def cargar_geojson(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ------------------- CARGA DE DATOS ---------------------

url_csv = "https://raw.githubusercontent.com/JesusParedes25/datasets/refs/heads/main/data1.xls"
df_original = cargar_csv(url_csv)
df_grouped = procesar_datos(df_original)
geojson_path = "Municipios.geojson"
municipios_geojson = cargar_geojson(geojson_path)

# ------------------- FILTROS ---------------------

# Quitamos el filtro de municipios

secretarias = sorted(df_grouped['secretaria'].unique())
secretaria_sel = st.sidebar.selectbox("Secretaría", ["Todas"] + secretarias)

if secretaria_sel != "Todas":
    dependencias_validas = df_grouped[df_grouped['secretaria'] == secretaria_sel]['dependencia'].unique()
else:
    dependencias_validas = df_grouped['dependencia'].unique()

dependencia_sel = st.sidebar.selectbox("Dependencia", ["Todas"] + sorted(dependencias_validas))

df_filtrado_temp = df_grouped.copy()

if secretaria_sel != "Todas":
    df_filtrado_temp = df_filtrado_temp[df_filtrado_temp['secretaria'] == secretaria_sel]
if dependencia_sel != "Todas":
    df_filtrado_temp = df_filtrado_temp[df_filtrado_temp['dependencia'] == dependencia_sel]

tramites_validos = sorted(set(t for sublist in df_filtrado_temp['nombre'] for t in sublist))
tramite_sel = st.sidebar.selectbox("Trámite", ["Todos"] + tramites_validos)

df_final = df_grouped.copy()

if secretaria_sel != "Todas":
    df_final = df_final[df_final['secretaria'] == secretaria_sel]
if dependencia_sel != "Todas":
    df_final = df_final[df_final['dependencia'] == dependencia_sel]
if tramite_sel != "Todos":
    df_final = df_final[df_final['nombre'].apply(lambda x: tramite_sel in x)]

solo_pachuca = st.sidebar.checkbox("Mostrar solo Pachuca De Soto")

if solo_pachuca:
    df_final = df_final[df_final['direccion'].str.contains("Pachuca De Soto", na=False)]

# Exportador
st.sidebar.download_button(
    label="Descargar datos filtrados",
    data=df_final.to_csv(index=False).encode('utf-8'),
    file_name='resultados_filtrados.csv',
    mime='text/csv'
)

# ------------------- MAPA ---------------------

pachuca_coords = [20.1011, -98.7591]
m = folium.Map(location=pachuca_coords, zoom_start=10)

# Dibujamos el geojson de municipios sin aplicar filtro
for feature in municipios_geojson['features']:
    nombre_municipio = feature['properties']['NOMGEO']

    color = '#ff0000' if nombre_municipio == "Pachuca de Soto" else '#666666'
    fill_color = '#ffff00' if nombre_municipio == "Pachuca de Soto" else '#dddddd'
    fill_opacity = 0.2 if nombre_municipio == "Pachuca de Soto" else 0.05
    weight = 3 if nombre_municipio == "Pachuca de Soto" else 1

    folium.GeoJson(
        feature,
        style_function=lambda feature, color=color, fill_color=fill_color, fill_opacity=fill_opacity, weight=weight: {
            'fillColor': fill_color,
            'color': color,
            'weight': weight,
            'fillOpacity': fill_opacity
        }
    ).add_to(m)

# Diccionario de colores por Secretaría
secretaria_colores = {
    'Secretaría de Gobierno': 'blue',
    'Secretaría de Contraloría': 'green',
    'Organismos No Sectorizados': 'orange',
    'Secretaría de Infraestructura Pública y Desarrollo Urbano Sostenible': 'purple',
    'Secretaría de Finanzas Públicas': 'red'
}

# MarkerCluster
marker_cluster = MarkerCluster().add_to(m)

# ------------------- MARCADORES ---------------------

for _, row in df_final.iterrows():
    try:
        lat = float(row['coordenada_y'])
        lon = float(row['coordenada_x'])
        color = secretaria_colores.get(row['secretaria'], "cadetblue")

        # Popup modernizado institucional
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; width: 320px; border: 1px solid #cccccc; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
            <div style="background-color:#9f2241; color:white; padding:8px; border-top-left-radius:8px; border-top-right-radius:8px;">
                Información del Punto de Atención
            </div>
            <div style="padding: 10px;">
                <b>Secretaría:</b><br> {row['secretaria']}<br><br>
                <b>Dependencia:</b><br> {row['dependencia']}<br><br>
                <b>Dirección:</b><br> {row['direccion']}<br><br>
                <b>Trámites:</b>
                <ul style="padding-left:20px; margin:0;">
                    {''.join(f'<li>{t}</li>' for t in row['nombre'])}
                </ul>
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=400),
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(marker_cluster)
    except Exception as e:
        print(f"Error: {e}")

# Mostrar mapa sin rerender en movimiento:
st_folium(m, use_container_width=True, height=800)


# In[ ]:





# In[ ]:




