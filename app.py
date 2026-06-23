import streamlit as st
import pandas as pd
import numpy as np
import cv2
import pydeck as pdk
from datetime import datetime
import time

# Configuración de la interfaz de usuario
st.set_page_config(page_title="Sistema de Gestión Temática", layout="wide")

# Estilos profesionales personalizados
st.markdown("""
    <style>
        .main-title { font-size: 2.4rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.2rem; }
        .subtitle { font-size: 1.05rem; color: #94a3b8; margin-bottom: 2rem; }
        .card-header { font-size: 1.2rem; font-weight: 600; color: #f1f5f9; margin-bottom: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Plataforma Central de Monitoreo Telemático</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Panel operativo para la supervisión de unidades, rastreo satelital y análisis óptico en tránsito.</p>', unsafe_allow_html=True)

# Inicialización de estados globales si no existen
if "coordenadas_alfa" not in st.session_state:
    st.session_state.coordenadas_alfa = {"lat": 19.6644, "lon": -99.0986}
if "coordenadas_beta" not in st.session_state:
    st.session_state.coordenadas_beta = {"lat": 19.6600, "lon": -99.1050}

# Menú de control lateral
with st.sidebar:
    st.markdown("### Control de Operaciones")
    with st.container(border=True):
        st.markdown("**Unidad Alfa**")
        monitorear_alfa = st.toggle("Enlazar Canal Alfa", value=False)
    
    with st.container(border=True):
        st.markdown("**Unidad Beta**")
        monitorear_beta = st.toggle("Enlazar Canal Beta", value=False)

# Cuadro de Indicadores de Rendimiento (KPIs)
unidades_en_servicio = sum([monitorear_alfa, monitorear_beta])
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

col_kpi1.metric(label="Unidades Activas", value=f"{unidades_en_servicio} / 2")
col_kpi2.metric(label="Estado del Núcleo", value="Operacional", delta="Conexión Segura")
col_kpi3.metric(label="Alertas del Sistema", value="0", delta="Normal", delta_color="inverse")
col_kpi4.metric(label="Hora del Servidor", value=datetime.now().strftime("%H:%M:%S"))

st.markdown("---")

# Organización modular del panel
col_telemetria, col_cartografia = st.columns([1, 1], gap="large")

with col_telemetria:
    st.markdown('<p class="card-header">Transmisiones de Video Activas</p>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("**Cámara de Seguridad - Unidad Alfa**")
        visor_alfa = st.empty()
        if not monitorear_alfa:
            visor_alfa.info("Canal Alfa fuera de línea de forma segura.")

    with st.container(border=True):
        st.markdown("**Cámara de Seguridad - Unidad Beta**")
        visor_beta = st.empty()
        if not monitorear_beta:
            visor_beta.info("Canal Beta fuera de línea de forma segura.")

with col_cartografia:
    st.markdown('<p class="card-header">Despliegue Geospacial de Unidades</p>', unsafe_allow_html=True)
    with st.container(border=True):
        mapa_operativo = st.empty()

# Lógica de actualización en tiempo real
if monitorear_alfa or monitorear_beta:
    while monitorear_alfa or monitorear_beta:
        
        # --- RECEPCIÓN Y RENDERIZADO DE VIDEO ---
        # En producción, aquí se procesan las imágenes enviadas por la ESP32-CAM
        if monitorear_alfa:
            # Reemplazar con el stream real de la ESP32-CAM en producción
            marco_simulado_alfa = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(marco_simulado_alfa, "Streaming Inalámbrico Alfa", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            visor_alfa.image(marco_simulado_alfa, channels="RGB", use_container_width=True)
            
            # Movimiento logístico simulado (hasta conectar el NEO-6M real)
            st.session_state.coordenadas_alfa["lat"] += np.random.uniform(-0.0001, 0.0001)
            st.session_state.coordenadas_alfa["lon"] += np.random.uniform(-0.0001, 0.0001)

        if monitorear_beta:
            marco_simulado_beta = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(marco_simulado_beta, "Streaming Inalámbrico Beta", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            visor_beta.image(marco_simulado_beta, channels="RGB", use_container_width=True)
            
            st.session_state.coordenadas_beta["lat"] += np.random.uniform(-0.0001, 0.0001)
            st.session_state.coordenadas_beta["lon"] += np.random.uniform(-0.0001, 0.0001)

        # --- CONSTRUCCIÓN DE CAPAS CARTOGRÁFICAS ---
        registros_gps = []
        if monitorear_alfa:
            registros_gps.append({"lat": st.session_state.coordenadas_alfa["lat"], "lon": st.session_state.coordenadas_alfa["lon"], "unidad": "Unidad Alfa", "color": [220, 38, 38, 220]})
        if monitorear_beta:
            registros_gps.append({"lat": st.session_state.coordenadas_beta["lat"], "lon": st.session_state.coordenadas_beta["lon"], "unidad": "Unidad Beta", "color": [37, 99, 235, 220]})

        df_posiciones = pd.DataFrame(registros_gps)

        if not df_posiciones.empty:
            capa_marcadores = pdk.Layer(
                "ScatterplotLayer",
                df_posiciones,
                get_position="[lon, lat]",
                get_color="color",
                get_radius=30,
            )
            
            capa_etiquetas = pdk.Layer(
                "TextLayer",
                df_posiciones,
                get_position="[lon, lat]",
                get_text="unidad",
                get_color=[255, 255, 255, 255],
                get_size=14,
                get_alignment_baseline="'bottom'",
            )
            
            # Centroide dinámico enfocado en las unidades operativas
            lat_centro = df_posiciones["lat"].mean()
            lon_centro = df_posiciones["lon"].mean()
            
            vista_mapa = pdk.ViewState(latitude=lat_centro, longitude=lon_centro, zoom=14, pitch=15)
            
            pila_mapas = pdk.Deck(
                map_style="dark",
                layers=[capa_marcadores, capa_etiquetas],
                initial_view_state=vista_mapa
            )
            mapa_operativo.pydeck_chart(pila_mapas)
        
        time.sleep(0.1)