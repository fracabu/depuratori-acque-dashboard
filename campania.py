import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import folium_static
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Costanti
CAMPANIA_CENTER = (40.8399, 14.2525)

@dataclass
class AppConfig:
    page_title: str = "Dashboard Depuratori Campania"
    page_icon: str = "💧"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    map_width: int = 1400
    map_height: int = 600

class StyleManager:
    @staticmethod
    def apply_custom_styles():
        st.markdown(
            """
            <style>
            .main-header {
                text-align: center;
                padding: 2rem;
                background: linear-gradient(135deg, #1E3D59 0%, #2E5E88 100%);
                color: white;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .main-header h1 {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            .main-header p {
                font-size: 1.2rem;
                opacity: 0.9;
            }
            .metric-card {
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_header():
        st.markdown(
            """
            <div class="main-header">
                <h1>Monitoraggio Depuratori - Regione Campania</h1>
                <p>Sistema di Visualizzazione e Analisi dei Depuratori Regionali</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

class DataProcessor:
    @staticmethod
    def load_and_process_data(uploaded_file):
        try:
            # Carica il file principale
            df = pd.read_csv(uploaded_file)
            
            # Carica il file delle coordinate
            coord_df = pd.read_csv("data/depuratori_campania_con_coordinate.csv")
            
            # Pulizia dati
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Converti i valori NaN in stringhe vuote per le colonne di testo
                    df[col] = df[col].fillna('')
                    
            # Standardizza i nomi dei comuni
            df['COMUNE'] = df['COMUNE'].str.strip().str.upper()
            coord_df['COMUNE'] = coord_df['COMUNE'].str.strip().str.upper()
            
            # Debug: mostra informazioni sui dati
            st.write("Colonne nel file principale:", df.columns.tolist())
            st.write("Numero di righe nel file principale:", len(df))
            
            # Unisci i dataframe
            merged_df = pd.merge(
                df, 
                coord_df[['COMUNE', 'LAT', 'LON']], 
                on='COMUNE',
                how='left'
            )
            
            # Debug: mostra informazioni sul merge
            st.write("Numero di righe dopo il merge:", len(merged_df))
            st.write("Righe con coordinate:", merged_df['LAT'].notna().sum())
            
            # Converti campi numerici
            if 'Potenz. (A.E.)' in merged_df.columns:
                merged_df['Potenz. (A.E.)'] = pd.to_numeric(
                    merged_df['Potenz. (A.E.)'].astype(str).str.replace(',', ''), 
                    errors='coerce'
                )
            
            return merged_df
            
        except Exception as e:
            logger.error(f"Errore nel processamento dei dati: {str(e)}")
            st.error(f"Errore nel caricamento dei dati: {str(e)}")
            return None

class MapVisualizer:
    @staticmethod
    def create_map(df: pd.DataFrame):
        st.subheader("Mappa Interattiva dei Depuratori")
        
        # Debug: mostra le colonne disponibili
        st.write("Colonne disponibili:", df.columns.tolist())
        
        # Debug: mostra alcuni dati di esempio
        st.write("Esempio dati:", df.head(1).to_dict('records'))
        
        # Verifica la presenza delle coordinate
        df_map = df.dropna(subset=['LAT', 'LON'])
        
        if df_map.empty:
            st.warning("Nessuna coordinata disponibile per visualizzare i depuratori.")
            return
            
        # Info sul numero di depuratori mappati
        st.info(f"📍 Depuratori mappati: {len(df_map)} su {len(df)} totali")

        # Crea la mappa base
        m = folium.Map(
            location=CAMPANIA_CENTER,
            zoom_start=8,
            tiles='CartoDB positron'
        )

        # Aggiungi i marker alla mappa
        for _, row in df_map.iterrows():
            popup_content = f"""
            <div style='min-width: 200px; max-width: 300px;'>
                <h4 style='margin: 0 0 10px 0;'>{row['COMUNE']}</h4>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr><td><b>Provincia:</b></td><td>{row['PROVINCIA']}</td></tr>
                    <tr><td><b>Indirizzo:</b></td><td>{row['INDIRIZZO']}</td></tr>
                    <tr><td><b>Tipologia:</b></td><td>{row['Tipologia Impianto']}</td></tr>
                    <tr><td><b>Reflui:</b></td><td>{row['Reflui Trattati']}</td></tr>
                    <tr><td><b>Potenzialità:</b></td><td>{row['Potenz. (A.E.)']}</td></tr>
                    <tr><td><b>Recettore:</b></td><td>{row['Recettore Finale']}</td></tr>
                    <tr><td><b>Data Sopralluogo:</b></td><td>{row['Data Sopralluogo']}</td></tr>
                    <tr><td><b>Esito:</b></td><td>{row['Esito Prelievo']}</td></tr>
                    <tr><td><b>Note:</b></td><td>{row['NOTE']}</td></tr>
                </table>
            </div>
            """

            folium.CircleMarker(
                location=(row['LAT'], row['LON']),
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='blue',
                fill=True,
                fillColor='blue',
                fillOpacity=0.7
            ).add_to(m)

        # Aggiungi controlli alla mappa
        folium.LayerControl().add_to(m)
        
        # Mostra la mappa
        folium_static(m, width=AppConfig.map_width, height=AppConfig.map_height)

    @staticmethod
    def _add_marker(cluster, row):
        """Aggiunge un marker alla mappa con tutte le informazioni disponibili"""
        # Prepara il contenuto del popup
        popup_content = f"""
        <div style='font-family: Arial; padding: 10px; min-width: 300px; max-height: 400px; overflow-y: auto;'>
            <h4 style='margin-bottom: 10px; color: #2C3E50; border-bottom: 2px solid #3498db; padding-bottom: 5px;'>
                {row['COMUNE']}
            </h4>
            <table style='width: 100%; border-collapse: collapse; font-size: 12px;'>
                <style>
                    tr:nth-child(even) {{background-color: #f8f9fa;}}
                    td {{padding: 4px 6px;}}
                    td:first-child {{font-weight: bold; color: #2C3E50; width: 40%;}}
                </style>
        """
        
        # Aggiungi tutti i campi disponibili al popup
        for col in row.index:
            if col not in ['LAT', 'LON'] and pd.notna(row[col]):
                value = row[col]
                if isinstance(value, (int, float)):
                    value = f"{value:,}"
                elif isinstance(value, str) and value.strip():
                    value = value.strip()
                else:
                    continue
                
                popup_content += f"""
                <tr>
                    <td>{col}:</td>
                    <td>{value}</td>
                </tr>
                """
        
        popup_content += """
            </table>
        </div>
        """
        
        # Crea il marker
        folium.CircleMarker(
            location=(row['LAT'], row['LON']),
            radius=8,
            popup=folium.Popup(popup_content, max_width=300),
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.7,
            weight=2
        ).add_to(cluster)

class Dashboard:
    def __init__(self):
        self.style_manager = StyleManager()

    def initialize(self):
        st.set_page_config(
            page_title=AppConfig.page_title,
            page_icon=AppConfig.page_icon,
            layout=AppConfig.layout,
            initial_sidebar_state=AppConfig.initial_sidebar_state,
        )
        self.style_manager.apply_custom_styles()
        self.style_manager.render_header()

    def run(self):
        self.initialize()

        st.sidebar.title("Controlli")
        uploaded_file = st.sidebar.file_uploader(
            "Carica un file CSV",
            type=['csv'],
            help="Carica il file CSV contenente i dati dei depuratori"
        )

        if uploaded_file:
            df = DataProcessor.load_and_process_data(uploaded_file)
            if df is not None:
                self._show_dashboard_components(df)
        else:
            self._show_welcome_message()

    def _show_dashboard_components(self, df: pd.DataFrame):
        # Mostra la mappa
        MapVisualizer.create_map(df)
        
        # Mostra statistiche e grafici
        self._show_statistics(df)
        self._show_data_analysis(df)
        
        # Mostra tabella dati
        self._show_data_table(df)

    def _show_statistics(self, df: pd.DataFrame):
        st.subheader("Statistiche Generali")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Totale Depuratori", len(df))
        with col2:
            st.metric("Comuni Serviti", df['COMUNE'].nunique())
        with col3:
            if 'Potenz. (A.E.)' in df.columns:
                total_ae = df['Potenz. (A.E.)'].sum()
                st.metric("Potenzialità Totale (A.E.)", f"{int(total_ae):,}")

    def _show_data_analysis(self, df: pd.DataFrame):
        st.subheader("Analisi dei Dati")

        col1, col2 = st.columns(2)
        
        with col1:
            if 'PROVINCIA' in df.columns:
                fig1, ax1 = plt.subplots(figsize=(10, 6))
                province_counts = df['PROVINCIA'].value_counts()
                sns.barplot(x=province_counts.values, y=province_counts.index)
                plt.title("Distribuzione per Provincia")
                plt.xlabel("Numero di Depuratori")
                st.pyplot(fig1)

        with col2:
            if 'Tipologia Impianto' in df.columns:
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                tipo_counts = df['Tipologia Impianto'].value_counts()
                plt.pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%')
                plt.title("Distribuzione per Tipologia Impianto")
                st.pyplot(fig2)

    def _show_data_table(self, df: pd.DataFrame):
        st.subheader("Tabella Dati")
        
        # Aggiungi filtri
        col1, col2 = st.columns(2)
        
        with col1:
            if 'PROVINCIA' in df.columns:
                # Gestisci valori nulli per provincia
                provincie = df['PROVINCIA'].dropna().unique()
                provincie = [p for p in provincie if isinstance(p, str)]
                province = ['Tutte'] + sorted(provincie)
                provincia_filter = st.selectbox('Filtra per Provincia:', province)

        with col2:
            if 'Tipologia Impianto' in df.columns:
                # Gestisci valori nulli per tipologia
                tipologie = df['Tipologia Impianto'].dropna().unique()
                tipologie = [t for t in tipologie if isinstance(t, str)]
                tipi = ['Tutti'] + sorted(tipologie)
                tipo_filter = st.selectbox('Filtra per Tipologia:', tipi)

        # Applica i filtri
        df_filtered = df.copy()
        if 'PROVINCIA' in df.columns and provincia_filter != 'Tutte':
            df_filtered = df_filtered[df_filtered['PROVINCIA'] == provincia_filter]
        if 'Tipologia Impianto' in df.columns and tipo_filter != 'Tutti':
            df_filtered = df_filtered[df_filtered['Tipologia Impianto'] == tipo_filter]

        # Mostra la tabella filtrata
        st.dataframe(df_filtered, use_container_width=True)

    def _show_welcome_message(self):
        st.info(
            """
            👋 Benvenuto nel sistema di monitoraggio dei depuratori della Campania!
            
            Per iniziare, carica il file CSV contenente i dati dei depuratori utilizzando 
            il pannello sulla sinistra.
            """
        )

if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run()