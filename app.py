import streamlit as st
import pandas as pd
import numpy as np
import cv2
import pydeck as pdk
from datetime import datetime
import time

# Configuración de la interfaz de usuario
st.set_page_config(page_title="Sistema de Gestión", layout="wide")

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
        # Campo dinámico para la IP (Si pones 0, usa la cámara web local)
        ip_alfa = st.text_input("URL de Video / WebCam (Ej: 0)", value="0", key="ip_alfa")
        monitorear_alfa = st.toggle("Enlazar Canal Alfa", value=False)
    
    with st.container(border=True):
        st.markdown("**Unidad Beta**")
        ip_beta = st.text_input("URL de Video / WebCam", value="", key="ip_beta")
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
    
    # --- INICIALIZACIÓN DE CÁMARAS ---
    # Convertimos el texto a número si el usuario ingresó un solo dígito (ej: "0" para la webcam)
    cap_alfa = None
    if monitorear_alfa and ip_alfa.strip() != "":
        fuente_alfa = int(ip_alfa) if ip_alfa.strip().isdigit() else ip_alfa
        cap_alfa = cv2.VideoCapture(fuente_alfa)
        
    cap_beta = None
    if monitorear_beta and ip_beta.strip() != "":
        fuente_beta = int(ip_beta) if ip_beta.strip().isdigit() else ip_beta
        cap_beta = cv2.VideoCapture(fuente_beta)

    while monitorear_alfa or monitorear_beta:
        
        # --- RECEPCIÓN Y RENDERIZADO DE VIDEO ALFA ---
        if monitorear_alfa:
            if cap_alfa and cap_alfa.isOpened():
                ret_a, frame_a = cap_alfa.read()
                if ret_a:
                    # OpenCV lee en BGR, Streamlit necesita RGB
                    frame_a_rgb = cv2.cvtColor(frame_a, cv2.COLOR_BGR2RGB)
                    visor_alfa.image(frame_a_rgb, channels="RGB", use_container_width=True)
                else:
                    visor_alfa.error("Pérdida de señal de video Alfa.")
            else:
                visor_alfa.warning("Intentando establecer conexión con la IP Alfa...")

            # Movimiento logístico simulado (hasta conectar el NEO-6M real)
            st.session_state.coordenadas_alfa["lat"] += np.random.uniform(-0.0001, 0.0001)
            st.session_state.coordenadas_alfa["lon"] += np.random.uniform(-0.0001, 0.0001)

        # --- RECEPCIÓN Y RENDERIZADO DE VIDEO BETA ---
        if monitorear_beta:
            if cap_beta and cap_beta.isOpened():
                ret_b, frame_b = cap_beta.read()
                if ret_b:
                    frame_b_rgb = cv2.cvtColor(frame_b, cv2.COLOR_BGR2RGB)
                    visor_beta.image(frame_b_rgb, channels="RGB", use_container_width=True)
                else:
                    visor_beta.error("Pérdida de señal de video Beta.")
            else:
                visor_beta.warning("Intentando establecer conexión con la IP Beta...")

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
        
        # Pequeña pausa para no saturar el procesador
        time.sleep(0.05)
