import pandas as pd

def check_missing_coords():
    df_full = pd.read_csv("data/Elenco_impianti_depurazione_Veneto_normalizzato.csv")
    df_coords = pd.read_csv("data/depuratori_con_coordinate.csv")
    
    missing = df_full[~df_full['SIT_ID'].isin(df_coords['SIT_ID'])]
    print(f"Depuratori senza coordinate: {len(missing)}")
    print("\nEsempi di indirizzi mancanti:")
    print(missing[['COMUNE', 'INDIRIZZO', 'TOPONIMO']].head())
    
    return missing

missing_coords = check_missing_coords()