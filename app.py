import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Dashboard Depuratori ML",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Stile generale */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3D59 0%, #2E5077 100%);
        padding: 2rem 1rem;
    }
    .stSidebar [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Header e titoli */
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4rem 0;
        position: relative;
        background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7));
        background-size: cover;
        background-position: center;
        margin: -6rem -4rem 2rem -4rem;
        color: white;
        min-height: 300px;
    }
    .title-container {
        text-align: center;
        padding: 2rem;
        z-index: 1;
    }
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .subtitle {
        font-size: 1.8rem;
        color: #E0E0E0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-container">
        <div class="title-container">
            <h1 class="main-title">Monitoraggio Nazionale Depuratori</h1>
            <p class="subtitle">Sistema di Analisi e Visualizzazione Dati</p>
        </div>
    </div>
""", unsafe_allow_html=True)

class DataProcessor:
    """Gestisce il caricamento e la preparazione dei dati"""

    geolocator = Nominatim(user_agent="streamlit-depurators")

    @staticmethod
    def _map_tipo_trattamento(code):
        """Mappa i codici numerici ai tipi di trattamento"""
        mapping = {
            1: "Primario",
            2: "Secondario",
            3: "Terziario"
        }
        return mapping.get(code, f"Tipo {code}")

    @staticmethod
    def geocode_location(location):
        """Effettua la geocodifica per una località"""
        try:
            location_data = DataProcessor.geolocator.geocode(location, timeout=10)
            if location_data:
                return location_data.latitude, location_data.longitude
            else:
                return None, None
        except GeocoderTimedOut:
            return None, None

    @staticmethod
    @st.cache_data(ttl=3600)
    def load_and_process_data(uploaded_file):
        
        try:
            # Leggi il CSV
            df = pd.read_csv(uploaded_file)

            # Verifica le colonne necessarie
            required_columns = ['id', 'area_riferimento', 'tipo_trattamento', 'anno', 'valore_osservato']
            if not all(col in df.columns for col in required_columns):
                st.error("Il file non contiene tutte le colonne necessarie")
                return None

            # Mappa i codici dei tipi di trattamento alle descrizioni
            df['tipo_trattamento_desc'] = df['tipo_trattamento'].map(DataProcessor._map_tipo_trattamento)

            # Geocodifica dinamica
            coordinates = []
            for area in df['area_riferimento'].unique():
                lat, lon = DataProcessor.geocode_location(area)
                coordinates.append({"area_riferimento": area, "LAT": lat, "LON": lon})

            coords_df = pd.DataFrame(coordinates)
            df = pd.merge(df, coords_df, on="area_riferimento", how="left")

            # Calcola l'efficienza
            df['EFFICIENCY'] = df.groupby(['area_riferimento', 'anno'])['valore_osservato'].transform(
                lambda x: (x / x.max() * 100)
            ).round(2)

            # Status default
            df['STATUS'] = 'Attivo'

            return df

        except Exception as e:
            st.error(f"Errore nel caricamento dei dati: {str(e)}")
            return None

class Dashboard:
    """Gestisce l'interfaccia utente della dashboard"""

    def show_filters(self, df):
        """Mostra e gestisce i filtri della dashboard"""
        with st.sidebar:
            st.markdown("### Filtri Analisi")

            # Filtro anno
            anni = sorted(df['anno'].unique())
            anno_default = anni[-1] if anni else None
            anno = st.selectbox(
                "Anno",
                options=anni,
                index=anni.index(anno_default) if anno_default else 0
            )

            # Filtro tipo trattamento usando le descrizioni
            tipi = st.multiselect(
                "Tipo Trattamento",
                options=sorted(df['tipo_trattamento_desc'].unique())
            )

            # Filtro area
            aree = st.multiselect(
                "Area",
                options=sorted(df['area_riferimento'].unique())
            )

        # Applicazione filtri
        mask = df['anno'] == anno
        if tipi:
            mask &= df['tipo_trattamento_desc'].isin(tipi)
        if aree:
            mask &= df['area_riferimento'].isin(aree)

        return df[mask]

    def show_metrics(self, df):
        """Mostra le metriche principali"""
        if len(df) > 0:
            latest_year = df['anno'].max()
            total_areas = df['area_riferimento'].nunique()
            total_value = df['valore_osservato'].sum()
            avg_efficiency = df['EFFICIENCY'].mean()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Anno di Riferimento", latest_year)
            with col2:
                st.metric("Aree Monitorate", total_areas)
            with col3:
                st.metric("Valore Totale", f"{total_value:,.0f}")
            with col4:
                st.metric("Efficienza Media", f"{avg_efficiency:.1f}%")
        else:
            st.warning("Nessun dato disponibile per il calcolo delle metriche.")

    def show_map(self, df):
        """Crea e mostra la mappa interattiva"""
        st.subheader("Mappa Nazionale Depuratori")

        df_map = df.dropna(subset=['LAT', 'LON'])

        if len(df_map) == 0:
            st.warning("Nessuna coordinata valida disponibile per la visualizzazione sulla mappa.")
            return

        # Centro della mappa sull'Italia
        m = folium.Map(location=[41.8719, 12.5674], zoom_start=6)
        marker_cluster = plugins.MarkerCluster().add_to(m)

        for _, row in df_map.iterrows():
            coords = (row['LAT'], row['LON'])
            popup_info = f"""
            <div>
                <b>Area:</b> {row['area_riferimento']}<br>
                <b>Tipo:</b> {row['tipo_trattamento_desc']}<br>
                <b>Anno:</b> {row['anno']}<br>
                <b>Valore:</b> {row['valore_osservato']}<br>
                <b>Efficienza:</b> {row['EFFICIENCY']}%
            </div>
            """
            folium.Marker(coords, popup=popup_info).add_to(marker_cluster)

        folium_static(m, width=1400, height=600)

    def show_charts(self, df):
        """Mostra i grafici principali"""
        if len(df) == 0:
            st.warning("Nessun dato disponibile per la visualizzazione dei grafici.")
            return

        col1, col2 = st.columns(2)

        with col1:
            df_pie = df.groupby('tipo_trattamento_desc')['valore_osservato'].sum().reset_index()
            fig_pie = px.pie(
                df_pie, values='valore_osservato', names='tipo_trattamento_desc',
                title='Distribuzione per Tipo di Trattamento'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            df_bar = df.groupby('area_riferimento')['valore_osservato'].sum().reset_index()
            fig_bar = px.bar(
                df_bar, x='area_riferimento', y='valore_osservato',
                title='Totale Valore per Area'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

def main():
    """Funzione principale dell'applicazione"""
    uploaded_file = st.sidebar.file_uploader(
        "Carica CSV Depuratori", 
        type=['csv'],
        help="Carica un file CSV con le colonne: id, area_riferimento, tipo_trattamento, anno, valore_osservato"
    )

    if uploaded_file is not None:
        df = DataProcessor.load_and_process_data(uploaded_file)

        if df is not None:
            dashboard = Dashboard()

            st.title("📊 Dashboard Depuratori")

            filtered_df = dashboard.show_filters(df)

            dashboard.show_metrics(filtered_df)
            dashboard.show_map(filtered_df)
            dashboard.show_charts(filtered_df)
            
            st.subheader("Dettaglio Dati")
            st.dataframe(
                filtered_df[[
                    'id', 'area_riferimento', 'tipo_trattamento_desc', 'anno',
                    'valore_osservato', 'EFFICIENCY'
                ]].sort_values(['anno', 'area_riferimento']),
                use_container_width=True
            )

            st.subheader("Analisi Temporale")
            trend_df = df.pivot_table(
                values='valore_osservato',
                index='anno',
                columns='tipo_trattamento_desc',
                aggfunc='sum'
            ).reset_index()

            fig = px.line(
                trend_df,
                x='anno',
                y=trend_df.columns[1:],
                title='Evoluzione Temporale per Tipo di Trattamento'
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Statistiche Descrittive")
            st.dataframe(
                df.groupby(['anno', 'tipo_trattamento_desc'])['valore_osservato']
                .describe()
                .round(2),
                use_container_width=True
            )
    else:
        st.info("""
            👋 Benvenuto nella Dashboard Nazionale Depuratori!
            
            Per iniziare:
            1. Carica un file CSV dalla barra laterale
            2. Il file deve contenere le colonne: id, area_riferimento, tipo_trattamento, anno, valore_osservato
            3. Usa i filtri per analizzare specifiche aree o periodi
        """)

    st.markdown("---")
    st.markdown(f"""
        <div style='text-align: center'>
            <small>Dashboard Nazionale Depuratori - Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


    
