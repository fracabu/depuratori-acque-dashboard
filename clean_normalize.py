import csv
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_dataset(input_file, output_file):
   """Normalizza un file CSV contenente dati dei depuratori del Veneto"""
   try:
       # Lettura del file originale con pandas 
       df = pd.read_csv(input_file, encoding='utf-8', dtype=str)

       # Pulizia colonne
       df.columns = df.columns.str.strip().str.replace('"', '')
       
       # Pulizia valori
       df = df.apply(lambda x: x.str.strip().str.replace('""', '"') if x.dtype == "object" else x)
       
       # Rimozione righe duplicate e vuote
       df = df.drop_duplicates()
       df = df.dropna(how='all')
       
       # Normalizzazione specifiche colonne
       if 'Numero Ab. Equiv. (AE)' in df.columns:
           df['Numero Ab. Equiv. (AE)'] = pd.to_numeric(
               df['Numero Ab. Equiv. (AE)'].str.replace(',', ''), 
               errors='coerce'
           )

       # Fix tipi di dati
       numeric_columns = ['SIT_ID', 'Numero Ab. Equiv. (AE)']
       for col in numeric_columns:
           if col in df.columns:
               df[col] = pd.to_numeric(df[col], errors='coerce')

       # Standardizzazione valori categorici
       categorical_columns = ['TIPO SCARICO', 'TIPO CORPO IDRICO', 'CLASSIFICAZIONE DEPURATORE', 
                            'STATO UNITA\' LOCALE', 'STATO DEPURATORE', 'STATO SCARICO']
       for col in categorical_columns:
           if col in df.columns:
               df[col] = df[col].str.title()

       # Salvataggio file normalizzato
       df.to_csv(output_file, index=False, encoding='utf-8')
       logger.info(f"Dataset normalizzato salvato in: {output_file}")
       
       # Log statistiche
       logger.info(f"Righe totali: {len(df)}")
       logger.info(f"Colonne: {', '.join(df.columns)}")

   except Exception as e:
       logger.error(f"Errore durante la normalizzazione: {e}")
       raise

if __name__ == "__main__":
   input_file = "data/Elenco_impianti_depurazione_Campania_agg_gen2024.csv"
   output_file = "data/Elenco_impianti_depurazione_Campania_normalizzato.csv"
   normalize_dataset(input_file, output_file)