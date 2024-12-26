import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time

def create_coordinates_file_campania():
    # Leggi il file CSV della Campania
    df = pd.read_csv("data/Elenco_impianti_depurazione_Campania_normalizzato.csv")
    
    # Verifica e modifica le colonne esistenti
    unique_locations = df[['COMUNE', 'INDIRIZZO']].drop_duplicates()
    
    geolocator = Nominatim(user_agent="campania_depuratori", timeout=30)
    coordinates = []
    failed = []
    
    for _, row in unique_locations.iterrows():
        success = False
        addresses = [
            f"{row['INDIRIZZO']}, {row['COMUNE']}, Campania, Italy",
            f"{row['COMUNE']}, Campania, Italy"
        ]
        
        for address in addresses:
            try:
                location = geolocator.geocode(address)
                if location:
                    coordinates.append({
                        'COMUNE': row['COMUNE'],
                        'INDIRIZZO': row['INDIRIZZO'],
                        'LAT': location.latitude,
                        'LON': location.longitude
                    })
                    print(f"✓ {row['COMUNE']} - {row['INDIRIZZO']}")
                    success = True
                    break
                time.sleep(2)
            except (GeocoderTimedOut, GeocoderUnavailable):
                print(f"✗ Errore: {row['COMUNE']} - {row['INDIRIZZO']}")
                time.sleep(5)
                continue
        
        if not success:
            failed.append(f"{row['COMUNE']} - {row['INDIRIZZO']}")
    
    pd.DataFrame(coordinates).to_csv("data/depuratori_campania_con_coordinate.csv", index=False)
    pd.DataFrame({'Error': failed}).to_csv("data/failed_geocoding_campania.csv", index=False)
    print(f"\nCoordinate generate: {len(coordinates)}/{len(unique_locations)}")


if __name__ == "__main__":
    create_coordinates_file_campania()
