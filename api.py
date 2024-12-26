import requests
import pandas as pd

# Elenco delle API regionali
API_REGIONALI = [
    {
        "nome": "ARPA Campania",
        "url": "https://dati.arpacampania.it/api/3/action/datastore_search",
        "resource_id": "a47b9842-1246-4d8f-b16a-d61bbabb782b"
    },
    # Aggiungi altre API regionali qui
]

# Funzione per raccogliere i dati da un'API regionale
def fetch_data(api_info, limit=1000):
    try:
        params = {
            "resource_id": api_info["resource_id"],
            "limit": limit
        }
        response = requests.get(api_info["url"], params=params)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("records", [])
            return pd.DataFrame(data)
        else:
            print(f"Errore API {api_info['nome']}: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Errore durante il fetch da {api_info['nome']}: {e}")
        return pd.DataFrame()

# Funzione per normalizzare i dati def normalizza_dati(df):
    # Rinominare colonne
    rename_map = {
        "Denominazione": "nome",
        "Comune": "comune",
        "Latitudine": "lat",
        "Longitudine": "lon",
        "Potenzialita_Progettuale": "capacita_progettuale",
        "Volume_Trattato": "volume_trattato",
        "Fanghi_Prodotti": "fanghi_prodotti",
        "Stato": "stato_attivo"
    }
    df = df.rename(columns=rename_map)

    # Rimuovere duplicati
    df = df.drop_duplicates()

    # Gestire valori mancanti (esempio: sostituire con 0 o valori medi)
    df = df.fillna({
        "capacita_progettuale": 0,
        "volume_trattato": 0,
        "fanghi_prodotti": 0
    })

    # Convalidare tipi di dato
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["capacita_progettuale"] = pd.to_numeric(df["capacita_progettuale"], errors="coerce")

    # Rimuovere record con coordinate non valide
    df = df[(df["lat"].between(-90, 90)) & (df["lon"].between(-180, 180))]

    return df

# Raccolta dati da tutte le API
all_data = []
for api in API_REGIONALI:
    df = fetch_data(api)
    if not df.empty:
        df["Fonte"] = api["nome"]  # Aggiungi la fonte dei dati
        all_data.append(df)

# Combina tutti i dati
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)

    # Normalizzare i dati
    normalized_df = normalizza_dati(combined_df)

    # Salva in un file CSV per un'analisi successiva
    normalized_df.to_csv("depuratori_normalizzati.csv", index=False)
    print("Dati normalizzati salvati in 'depuratori_normalizzati.csv'")
else:
    print("Nessun dato disponibile dalle API")

# Prossimi passi:
# 1. Creare un backend con FastAPI per servire questi dati.
# 2. Implementare endpoint per query specifiche.
