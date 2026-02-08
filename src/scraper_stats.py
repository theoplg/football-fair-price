import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import re  # Pour nettoyer le texte avec des expressions régulières

# 1. Charger la liste des joueurs (issue de l'étape 1)
nombre_de_pages = 50
try:
    df = pd.read_csv('data/raw/transfers_large_dataset.csv')
    print(f"Chargement de {len(df)} joueurs...")
except FileNotFoundError:
    print("Erreur : Lance l'étape 1 d'abord pour avoir le fichier transfers_large_dataset.csv")
    exit()

# Listes pour stocker les nouvelles données
positions = []
ages_corriges = []
minutes_jouees = []
buts = []
matchs_joues = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("--- Démarrage de la récupération des Stats & Ages ---")

# 2. Boucler sur chaque joueur
for index, row in df.iterrows():
    original_url = row['URL_Profil']
    nom = row['Nom']
    
    print(f"[{index+1}/{len(df)}] {nom}...", end="\r")
    
    # URL pour les stats (Saison 2022 pour les transferts 2023)
    # L'astuce : la page stats contient aussi le header avec l'âge et le poste
    stats_url = original_url.replace("profil", "leistungsdaten") + "/plus/0?saison=2022"
    
    # Valeurs par défaut
    pos_found = "Inconnu"
    age_found = row['Age'] # On part de l'âge qu'on avait
    
    # Si l'âge actuel est vide ou ressemble à une agence (pas un nombre), on le force à "Inconnu" pour le re-chercher
    if pd.isna(age_found) or not str(age_found).replace(" ", "").isdigit() or len(str(age_found)) > 3:
        age_found = "Inconnu"
        
    m_joues, b, mins = 0, 0, 0
    
    try:
        response = requests.get(stats_url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- A. RECUPERATION DE L'AGE (Méthode Robuste) ---
            # On cherche la balise sémantique 'birthDate'
            # Le texte ressemble souvent à : "22 janv. 1998 (25)"
            birth_span = soup.find('span', itemprop="birthDate")
            if birth_span:
                text = birth_span.text.strip()
                # On prend ce qu'il y a entre parenthèses
                if "(" in text and ")" in text:
                    age_found = text.split("(")[-1].replace(")", "")
                else:
                    # Parfois l'âge n'est pas entre parenthèses, on essaie de trouver un nombre
                    # Mais sur Transfermarkt fr, c'est quasi toujours (XX)
                    pass

            # --- B. RECUPERATION DU POSTE ---
            # On cherche la boite header
            header_box = soup.find('div', class_='data-header__details')
            if header_box:
                items = header_box.find_all('li', class_='data-header__label')
                for item in items:
                    text_label = item.text.strip()
                    if "Position" in text_label:
                        span = item.find('span', class_='data-header__content')
                        if span:
                            pos_found = span.text.strip()

            # --- C. RECUPERATION DES STATS ---
            table = soup.find('table', class_='items')
            if table:
                tfoot = table.find('tfoot')
                if tfoot:
                    cells = tfoot.find_all('td')
                    # Colonnes : Matchs(2), Buts(3), Minutes(Dernière)
                    # Attention aux index qui peuvent varier, mais c'est stable généralement
                    try:
                        m_joues = cells[2].text.strip().replace('-', '0')
                        b = cells[3].text.strip().replace('-', '0')
                        mins = cells[-1].text.strip().replace('.', '').replace("'", "").replace('-', '0')
                    except IndexError:
                        pass # Erreur de tableau, on garde 0

    except Exception as e:
        # En cas d'erreur réseau ou autre, on continue
        pass

    # Ajout aux listes
    positions.append(pos_found)
    ages_corriges.append(age_found)
    matchs_joues.append(m_joues)
    buts.append(b)
    minutes_jouees.append(mins)
    
    # Pause aléatoire pour ne pas se faire bloquer
    time.sleep(random.uniform(0.5, 1.5))

# 3. Mise à jour du DataFrame
df['Position'] = positions
df['Age'] = ages_corriges
df['Matchs_22_23'] = matchs_joues
df['Buts_22_23'] = buts
df['Minutes_22_23'] = minutes_jouees

# 4. Sauvegarde
output_file = 'data/processed/transfers_with_stats_final_.csv'
df.to_csv(output_file, index=False)
print(f"\n✅ Terminé ! Vérifie le fichier : {output_file}")
print(df[['Nom', 'Age', 'Position']].head(5))