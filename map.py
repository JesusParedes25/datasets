#!/usr/bin/env python
# coding: utf-8

# In[20]:


import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import json

# Leer CSV desde GitHub
url_csv = "https://raw.githubusercontent.com/JesusParedes25/datasets/refs/heads/main/data1.xls"
df_original = pd.read_csv(url_csv)

# Leer GeoJSON de municipios
geojson_path = "Municipios.geojson"
with open(geojson_path, encoding="utf-8") as f:
    municipios_geojson = json.load(f)

# Flatten sucursales
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

# Agrupación final
df_grouped = df_limpio.groupby(
    ['coordenada_x', 'coordenada_y', 'secretaria', 'dependencia']
).agg({
    'direccion': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
    'nombre': lambda x: list(set(x))
}).reset_index()

# Diccionario de colores por Secretaría (puedes ampliar este diccionario)
secretaria_colores = {
    'Secretaría de Gobierno': 'blue',
    'Secretaría de Contraloría': 'green',
    'Organismos No Sectorizados': 'orange',
    'Secretaría de Infraestructura Pública y Desarrollo Urbano Sostenible': 'purple',
    'Secretaría de Finanzas Públicas': 'red'
}

# Streamlit config
st.set_page_config(page_title="SIG de Trámites", layout="wide")

st.title("🗺️ Plataforma Interactiva de Trámites y Sucursales")

# Filtros

municipios = sorted([feat['properties']['NOMGEO'] for feat in municipios_geojson['features']])
municipio_sel = st.sidebar.selectbox("Municipio", ["Todos"] + municipios)

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

# Exportador de resultados filtrados
st.sidebar.download_button(
    label="Descargar datos filtrados",
    data=df_final.to_csv(index=False).encode('utf-8'),
    file_name='resultados_filtrados.csv',
    mime='text/csv'
)

# Mapa principal
pachuca_coords = [20.1011, -98.7591]
m = folium.Map(location=pachuca_coords, zoom_start=10)

# Municipios
for feature in municipios_geojson['features']:
    nombre_municipio = feature['properties']['NOMGEO']
    if municipio_sel == "Todos" or municipio_sel == nombre_municipio:
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

# Marcadores
for _, row in df_final.iterrows():
    try:
        lat = float(row['coordenada_y'])
        lon = float(row['coordenada_x'])
        tramites = "<br>".join(row['nombre'])
        color = secretaria_colores.get(row['secretaria'], "cadetblue")

        popup_html = f"""
        <div style="font-family: Arial; font-size: 13px;">
            <b>Dirección:</b> {row['direccion']}<br><br>
            <b>Trámites:</b><br>{tramites}<br>
            <b>Secretaría:</b> {row['secretaria']}<br>
            <b>Dependencia:</b> {row['dependencia']}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=400),
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
    except Exception as e:
        print(f"Error: {e}")

# Mostrar mapa a pantalla completa
st_folium(m, use_container_width=True, height=800)


# In[ ]:





# In[ ]:




