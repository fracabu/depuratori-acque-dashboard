import pandas as pd
import requests
import time

# Percorso del file
file_depuratori = "data/Dataset_Normalizzato_ISTAT_Depuratori_Acque.csv"
output_file = "data/depuratori_con_coordinate.csv"

# Chiave API di Azure Maps
api_key = "YOUR_AZURE_MAPS_API_KEY"

# Funzione di geocoding tramite Azure Maps
def get_coordinates_azure(query, api_key):
    url = "https://atlas.microsoft.com/search/address/json"
    params = {
        "api-version": "1.0",
        "subscription-key": api_key,
        "query": query + ", Italy",  # Utilizziamo anche "Italy" per migliorare la precisione
        "countrySet": "IT"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        if results:
            position = results[0].get('position', {})
            return position.get('lat'), position.get('lon')
    return None, None

# Carica il dataset dei depuratori
df_depuratori = pd.read_csv(file_depuratori, encoding="utf-8")

# Lista per memorizzare le coordinate geografiche
coordinates = []

# Geocoding per ogni depuratore
for index, row in df_depuratori.iterrows():
    location = row["area_riferimento"]  # Usa la colonna con la località
    lat, lon = get_coordinates_azure(location, api_key)
    coordinates.append((lat, lon))
    time.sleep(1)  # Evita di superare il limite delle chiamate API

# Aggiungi le coordinate al dataset
df_depuratori["Latitude"], df_depuratori["Longitude"] = zip(*coordinates)

# Salva il nuovo dataset con le coordinate geografiche
df_depuratori.to_csv(output_file, index=False, encoding="utf-8")
print(f"File CSV con le coordinate geografiche salvato in: {output_file}")
