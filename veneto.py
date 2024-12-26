import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from dataclasses import dataclass
from typing import Optional, Tuple, List
import logging
import time
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans # Esempio clustering


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VENETO_CENTER = (45.4347, 12.3384)
COLUMN_MAPPINGS = {
   "PROVINCIA": "Provincia",
   "COMUNE": "Comune",
   "SIT_ID": "ID_Sito",
   "DENOMINAZIONE UNITA' LOCALE": "Nome_Depuratore",
   "TIPO SCARICO": "Tipo_Scarico",
   "TIPO CORPO IDRICO": "Tipo_Corpo_Idrico",
   "NOME CORPO IDRICO RECETTORE": "Nome_Corpo_Idrico",
   "CLASSIFICAZIONE DEPURATORE": "Classificazione_Depuratore",
   "Numero Ab. Equiv. (AE)": "Numero_AE",
   "STATO UNITA' LOCALE": "Stato_Unita_Locale",
   "STATO DEPURATORE": "Stato_Depuratore",
   "STATO SCARICO": "Stato_Scarico",
}

@dataclass
class AppConfig:
   page_title: str = "Dashboard Depuratori Veneto"
   page_icon: str = "💧"
   layout: str = "wide"
   initial_sidebar_state: str = "expanded"
   map_width: int = 1400
   map_height: int = 600
   cache_ttl: int = 3600

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
               <h1>Monitoraggio Depuratori - Regione Veneto</h1>
               <p>Sistema Avanzato di Visualizzazione e Analisi dei Depuratori Regionali</p>
           </div>
           """,
           unsafe_allow_html=True,
       )

class DataProcessor:

    _coord_df = None  # Class variable to store the coordinates DataFrame

    @staticmethod
    def _load_coord_data():
        try:
            if DataProcessor._coord_df is None:
              DataProcessor._coord_df = pd.read_csv("data/depuratori_con_coordinate.csv")
            return DataProcessor._coord_df
        except FileNotFoundError:
            logger.error("File delle coordinate non trovato.")
            st.error("File delle coordinate non trovato.")
            return None
        except Exception as e:
            logger.error(f"Errore nel caricamento delle coordinate: {e}")
            st.error(f"Errore nel caricamento delle coordinate: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=AppConfig.cache_ttl)
    def load_and_process_data(uploaded_file) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_csv(uploaded_file)
            df = DataProcessor._rename_columns(df)
            df = DataProcessor._add_coordinates(df)
            df = DataProcessor._clean_and_transform_data(df)
            return df
        except Exception as e:
            logger.error(f"Errore nel processamento dei dati: {str(e)}")
            st.error(f"Errore nel caricamento dei dati: {str(e)}")
            return None

    @staticmethod
    def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=COLUMN_MAPPINGS)

    @staticmethod
    def _add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
        coord_df = DataProcessor._load_coord_data()
        if coord_df is None:
             return df
        try:
            df = pd.merge(df, coord_df[['SIT_ID', 'LAT', 'LON']],
                         left_on='ID_Sito',
                         right_on='SIT_ID',
                         how='left')
            df.drop('SIT_ID', axis=1, inplace=True)

            # Geocode missing coordinates
            missing_coords_df = df[df['LAT'].isna() | df['LON'].isna()]
            if not missing_coords_df.empty:
               df = DataProcessor._geocode_missing_coordinates(df)
            logger.info(f"Coordinate aggiunte per {df['LAT'].notna().sum()} depuratori")
            return df
        except Exception as e:
             logger.error(f"Errore nell'aggiunta delle coordinate: {e}")
             return df

    @staticmethod
    def _geocode_missing_coordinates(df: pd.DataFrame) -> pd.DataFrame:
       """
       Geocodes missing coordinates for depuratori based on their Comune.
       """
       geolocator = Nominatim(user_agent="depuratori_app", timeout=5)
       for index, row in df.iterrows():
            if pd.isna(row["LAT"]) or pd.isna(row["LON"]):
               try:
                    location = geolocator.geocode(row['Comune'] + ", Veneto, Italy", exactly_one=True)
                    if location:
                        df.loc[index, 'LAT'] = location.latitude
                        df.loc[index, 'LON'] = location.longitude
                        logger.info(f"Geocoded {row['Comune']}: {location.latitude}, {location.longitude}")
                    else:
                        logger.warning(f"Could not geocode: {row['Comune']}")
               except GeocoderTimedOut:
                   logger.warning(f"Geocoding timed out for: {row['Comune']}. Retrying...")
                   time.sleep(1) # Wait for one second before retry
                   try:
                       location = geolocator.geocode(row['Comune'] + ", Veneto, Italy", exactly_one=True, timeout=10)
                       if location:
                            df.loc[index, 'LAT'] = location.latitude
                            df.loc[index, 'LON'] = location.longitude
                            logger.info(f"Geocoded {row['Comune']} on retry: {location.latitude}, {location.longitude}")
                       else:
                             logger.warning(f"Could not geocode: {row['Comune']} even on retry")
                   except GeocoderTimedOut:
                       logger.error(f"Geocoding timed out even on retry: {row['Comune']}")
               except Exception as e:
                    logger.error(f"Errore geocoding {row['Comune']}: {e}")
       return df


    @staticmethod
    def _clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
       df["Numero_AE"] = pd.to_numeric(
           df["Numero_AE"].astype(str).str.replace(",", ""), errors="coerce"
       )
       string_columns = df.select_dtypes(include=["object"]).columns
       df[string_columns] = df[string_columns].apply(lambda x: x.str.strip())
       return df

class MapVisualizer:
   @staticmethod
   def create_map(df: pd.DataFrame):
       st.subheader("Mappa Interattiva dei Depuratori")

       df_map = df.dropna(subset=["LAT", "LON"])
       if df_map.empty:
           st.warning("Nessuna coordinata disponibile per visualizzare i depuratori.")
           return

       m = folium.Map(location=VENETO_CENTER, zoom_start=8)
       marker_cluster = plugins.MarkerCluster().add_to(m)

       for _, row in df_map.iterrows():
           MapVisualizer._add_marker(marker_cluster, row)

       folium.LayerControl().add_to(m) # Add layer control

       folium_static(m, width=AppConfig.map_width, height=AppConfig.map_height)

   @staticmethod
   def _add_marker(cluster, row):
       popup_content = f"""
       <div style='font-family: Arial; padding: 10px;'>
           <h4 style='margin-bottom: 10px;'>{row['Nome_Depuratore']}</h4>
           <table style='width: 100%;'>
               <tr><td><b>Comune:</b></td><td>{row['Comune']}</td></tr>
               <tr><td><b>Tipo Scarico:</b></td><td>{row['Tipo_Scarico']}</td></tr>
               <tr><td><b>Corpo Idrico:</b></td><td>{row['Nome_Corpo_Idrico']}</td></tr>
               <tr><td><b>AE:</b></td><td>{int(row['Numero_AE']) if pd.notnull(row['Numero_AE']) and str(row['Numero_AE']).isdigit() else 'N/A'}</td></tr>
               <tr><td><b>Stato:</b></td><td>{row['Stato_Unita_Locale']}</td></tr>
               <tr><td><b>Stato Depuratore:</b></td><td>{row['Stato_Depuratore']}</td></tr>
           </table>
       </div>
       """
       folium.Marker(
           location=(row["LAT"], row["LON"]),
           popup=folium.Popup(popup_content, max_width=300),
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

       uploaded_file = st.sidebar.file_uploader(
           "Carica un file CSV",
           type=["csv"],
           help="Carica un file CSV con i dati dei depuratori del Veneto",
       )

       if uploaded_file:
           df = DataProcessor.load_and_process_data(uploaded_file)
           if df is not None:
               self._show_dashboard_components(df)
       else:
           self._show_welcome_message()

   def _show_dashboard_components(self, df: pd.DataFrame):
       self._show_statistics(df)
       MapVisualizer.create_map(df)
       self._show_data_analysis(df)
       self._show_additional_visualizations(df)  # Chiamata alla funzione aggiunta
       self._show_predictions(df) #Chiamata alla funzione previsioni
       self._show_table(df)


   def _show_statistics(self, df: pd.DataFrame):
       col1, col2, col3, col4 = st.columns(4)

       with col1:
           st.metric("Totale Depuratori", len(df))
       with col2:
           st.metric("Provincie Coperte", df["Provincia"].nunique())
       with col3:
           st.metric("Comuni Serviti", df["Comune"].nunique())
       with col4:
           tot_ae = df["Numero_AE"].sum()
           st.metric("Totale AE", f"{int(tot_ae):,}")

   def _show_data_analysis(self, df: pd.DataFrame):
    st.subheader("Analisi dei Dati")
    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots()
        stato_counts = df["Stato_Depuratore"].value_counts()
        ax1.bar(stato_counts.index, stato_counts.values)
        plt.xticks(rotation=45, ha='right')
        plt.title("Distribuzione per Stato Depuratore")
        plt.tight_layout()
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots()
        scarico_counts = df["Tipo_Scarico"].value_counts()
        ax2.bar(scarico_counts.index, scarico_counts.values)
        plt.xticks(rotation=45, ha='right')
        plt.title("Distribuzione per Tipo Scarico")
        plt.tight_layout()
        st.pyplot(fig2)

    st.write("#### Stima della Portata (m³/giorno)")
    df["Portata_m3_giorno"] = df["Numero_AE"] * 0.2
    portata_totale = df["Portata_m3_giorno"].sum()
    st.metric("Portata Totale Regionale (m³/giorno)", f"{portata_totale:,.0f}")

    fig3, ax3 = plt.subplots()
    portata_per_provincia = df.groupby("Provincia")["Portata_m3_giorno"].sum()
    ax3.bar(portata_per_provincia.index, portata_per_provincia.values)
    plt.xticks(rotation=45, ha='right')
    plt.title("Portata per Provincia")
    plt.tight_layout()
    st.pyplot(fig3)

   def _show_additional_visualizations(self, df: pd.DataFrame):
       st.subheader("Visualizzazioni Aggiuntive")
       col1, col2 = st.columns(2)

       with col1:
           st.write("#### Depuratori per Provincia")
           provincia_counts = df["Provincia"].value_counts().sort_index()
           st.bar_chart(provincia_counts)

       with col2:
           st.write("#### Distribuzione AE per Provincia (Box Plot)")
           fig_bp, ax_bp = plt.subplots()
           sns.boxplot(x="Provincia", y="Numero_AE", data=df, ax=ax_bp)
           ax_bp.tick_params(axis='x', rotation=45)
           st.pyplot(fig_bp)


       st.write("#### Percentuale per Tipo Scarico (Torta)")
       scarico_counts = df["Tipo_Scarico"].value_counts()
       fig_pie, ax_pie = plt.subplots()
       ax_pie.pie(scarico_counts, labels=scarico_counts.index, autopct='%1.1f%%', startangle=140)
       ax_pie.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
       st.pyplot(fig_pie)

   def _show_predictions(self, df: pd.DataFrame):
       st.subheader("Previsioni e Analisi Avanzate")

       # Esempio di calcolo di anomalie con K-means
       try:
           kmeans = KMeans(n_clusters=3, random_state=42, n_init = 'auto')  # Riduci n_init al default
           df_for_clustering = df[["Numero_AE", "Portata_m3_giorno"]].dropna()
           if not df_for_clustering.empty:
               kmeans.fit(df_for_clustering)
               df['cluster'] = pd.NA  # Inizializza la colonna cluster con NA
               df.loc[df_for_clustering.index, 'cluster'] = kmeans.labels_
               st.write("#### Analisi cluster basata su Numero_AE e Portata_m3_giorno:")
               st.write(df[["Nome_Depuratore", "Numero_AE", "Portata_m3_giorno", "cluster"]].dropna())
           else:
              st.warning("Non ci sono dati validi per effettuare la clusterizzazione.")
       except Exception as e:
            logger.error(f"Errore durante il calcolo dei cluster: {e}")
            st.warning(f"Errore durante il calcolo dei cluster: {e}")

       # Placeholder per altre previsioni
       st.write("#### Previsioni Portata Totale (Placeholder)")
       st.write(
           "Questo è un placeholder. Qui potrebbero essere mostrate previsioni "
           "della portata totale basate su modelli di machine learning, "
           "quando si avranno dati storici."
       )

   def _show_table(self, df: pd.DataFrame):
       st.subheader("Dati dei Depuratori")

       col1, col2, col3 = st.columns(3)
       with col1:
           provincia_filter = st.multiselect(
               "Filtra per Provincia", options=sorted(df["Provincia"].unique())
           )
       with col2:
           stato_filter = st.multiselect(
               "Filtra per Stato Depuratore",
               options=sorted(df["Stato_Depuratore"].unique()),
           )
       with col3:
           tipo_scarico_filter = st.multiselect(
               "Filtra per Tipo Scarico", options=sorted(df["Tipo_Scarico"].unique())
           )

       filtered_df = df.copy()
       if provincia_filter:
           filtered_df = filtered_df[filtered_df["Provincia"].isin(provincia_filter)]
       if stato_filter:
           filtered_df = filtered_df[filtered_df["Stato_Depuratore"].isin(stato_filter)]
       if tipo_scarico_filter:
           filtered_df = filtered_df[filtered_df["Tipo_Scarico"].isin(tipo_scarico_filter)]

       st.dataframe(
           filtered_df[[
               "Provincia", "Comune", "Nome_Depuratore", "Tipo_Scarico",
               "Nome_Corpo_Idrico", "Numero_AE", "Portata_m3_giorno",
               "Stato_Depuratore", "Stato_Scarico"
           ]],
           use_container_width=True,
       )

   def _show_welcome_message(self):
       st.info(
           "👋 Benvenuto nel sistema di monitoraggio dei depuratori del Veneto!\n\n"
           "Per iniziare, carica un file CSV contenente i dati dei depuratori "
           "utilizzando il pannello sulla sinistra."
       )

if __name__ == "__main__":
   dashboard = Dashboard()
   dashboard.run()