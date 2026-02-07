import pandas as pd
import re

# 1. Charger les données brutes
input_file = 'data/raw/transfers_with_stats_final.csv'
try:
    df = pd.read_csv(input_file)
    print(f"Chargement de {len(df)} lignes...")
except FileNotFoundError:
    print(f"Erreur : Le fichier {input_file} n'existe pas.")
    exit()

# --- FONCTIONS DE NETTOYAGE ---

def clean_price(price_str):
    """Convertit '60,00 mio. €' en 60000000"""
    if not isinstance(price_str, str):
        return None
    
    price_str = price_str.lower()
    
    # On exclut les prêts et les transferts libres (valeurs aberrantes pour un modèle de prix)
    if 'prêt' in price_str or 'libre' in price_str or '?' in price_str or '-' in price_str:
        return None
        
    # Gestion des Millions
    if 'mio' in price_str:
        clean_str = price_str.replace('mio.', '').replace('€', '').replace(',', '.').strip()
        try:
            return float(clean_str) * 1_000_000
        except:
            return None
            
    # Gestion des Milliers (k)
    if 'k' in price_str or 'th' in price_str:
        clean_str = price_str.replace('th.', '').replace('k', '').replace('€', '').replace(',', '.').strip()
        try:
            return float(clean_str) * 1_000
        except:
            return None
            
    return None

def clean_position(pos_str):
    """Encode le poste en chiffres : 1=Gardien, 2=Déf, 3=Milieu, 4=Att"""
    if not isinstance(pos_str, str):
        return None
        
    pos_str = pos_str.lower()
    
    if 'gardien' in pos_str:
        return 1
    elif 'défenseur' in pos_str or 'arrière' in pos_str:
        return 2
    elif 'milieu' in pos_str:
        return 3
    elif 'attaquant' in pos_str or 'ailier' in pos_str or 'avant-centre' in pos_str:
        return 4
    else:
        return None

# --- APPLICATION DU NETTOYAGE ---

# 1. Nettoyage du Prix
df['Prix'] = df['Prix_Raw'].apply(clean_price)

# 2. Nettoyage du Poste
df['Position_Encoded'] = df['Position'].apply(clean_position)

# 3. Nettoyage de l'Age (s'assurer que c'est un chiffre)
df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

# 4. Suppression des lignes inutilisables
# On enlève les joueurs dont on n'a pas réussi à trouver le prix (prêts/libres) ou l'âge
df_clean = df.dropna(subset=['Prix', 'Age', 'Position_Encoded'])

# 5. Sélection des colonnes finales pour le modèle
cols_to_keep = ['Nom', 'Age', 'Position_Encoded', 'Matchs_22_23', 'Buts_22_23', 'Minutes_22_23', 'Prix']
df_final = df_clean[cols_to_keep]

# Affichage des stats avant/après
print(f"\nLignes avant nettoyage : {len(df)}")
print(f"Lignes après nettoyage : {len(df_final)}")
print("\n--- Aperçu des données propres ---")
print(df_final.head())

# Sauvegarde
output_file = 'data/processed/transfers_cleaned.csv'
df_final.to_csv(output_file, index=False)
print(f"\n✅ Fichier propre sauvegardé : {output_file}")