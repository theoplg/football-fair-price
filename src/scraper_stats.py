import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os

# --- CONFIGURATION ---
FILE_RAW_LIST = 'data/raw/transfers_large_dataset.csv'
FILE_DATABASE = 'data/processed/transfers_v3.csv'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("--- DÉMARRAGE DE LA MISE À JOUR (Méthode Bulldozer) ---")

# 1. CHARGEMENT
try:
    df_new = pd.read_csv(FILE_RAW_LIST)
except:
    print("❌ Erreur : Pas de fichier liste.")
    exit()

if os.path.exists(FILE_DATABASE):
    df_existing = pd.read_csv(FILE_DATABASE)
    existing_urls = set(df_existing['URL_Profil'].tolist())
else:
    df_existing = pd.DataFrame()
    existing_urls = set()

# 2. FILTRAGE
players_to_scrape = df_new[~df_new['URL_Profil'].isin(existing_urls)].copy()

if len(players_to_scrape) == 0:
    print("\n✅ TOUT EST DÉJÀ À JOUR !")
    exit()

print(f"\n🚀 Nouveaux joueurs à traiter : {len(players_to_scrape)}")

# 3. SCRAPING
new_data = []

for index, row in players_to_scrape.iterrows():
    nom = row['Nom']
    url = row['URL_Profil']
    
    print(f"[{index+1}/{len(players_to_scrape)}] {nom}...", end="\r")
    
    stats_url = url.replace("profil", "leistungsdaten") + "/plus/0?saison=2022"
    
    player_data = row.to_dict()
    
    # Valeurs par défaut
    pos_found = "Inconnu"
    age_found = row['Age']
    ligue_found = "Autre"
    contrat_found = 0
    m_joues, b, mins = 0, 0, 0
    
    try:
        response = requests.get(stats_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # --- DEBUG : Est-ce qu'on est bloqué ? ---
            # Si le titre est bizarre, Transfermarkt nous a peut-être envoyé un Captcha
            if index == 0:
                print(f"\n[DEBUG] Titre de la page : {soup.title.text.strip()}")

            # =================================================================
            # 🔍 RECHERCHE DU CONTRAT : 3 MÉTHODES
            # =================================================================
            
            # --- MÉTHODE 1 : Header Classique ---
            header_box = soup.find('div', class_='data-header__details')
            if header_box:
                items = header_box.find_all('li')
                for item in items:
                    txt = item.text.strip() # On utilise 'txt'
                    
                    # Récupération du Poste
                    if "Position" in txt:
                         if item.find('span', class_='data-header__content'):
                            pos_found = item.find('span', class_='data-header__content').text.strip()
                    
                    # Récupération du Contrat (Correction ici)
                    if "Contrat" in txt or "Contract" in txt or "expires" in txt:
                        # On cherche une année à 4 chiffres (ex: 2024, 2030...)
                        years = re.findall(r'20\d{2}', txt)
                        if years:
                            contrat_found = int(years[0])

            # --- MÉTHODE 2 : Recherche dans les textes (au cas où le format du header change) ---
            if contrat_found == 0:
                label = soup.find(string=re.compile(r"Contrat jusqu'à|Contract expires"))
                if label:
                    parent_text = label.find_parent().text if label.find_parent() else label.parent.text
                    # Correction ICI aussi : 20\d{2} au lieu de 202\d
                    years = re.findall(r'20\d{2}', parent_text)
                    if years:
                        contrat_found = int(years[0])

            # --- MÉTHODE 3 : Tableau "Données et faits" ---
            if contrat_found == 0:
                table_info = soup.find('table', class_='auflistung')
                if table_info:
                    all_rows = table_info.find_all('tr')
                    for tr in all_rows:
                        if "Contrat" in tr.text:
                            # Correction ICI aussi
                            years = re.findall(r'20\d{2}', tr.text)
                            if years: contrat_found = int(years[0])
            # =================================================================
            # FIN RECHERCHE CONTRAT
            # =================================================================

            # Age
            birth_span = soup.find('span', itemprop="birthDate")
            if birth_span:
                text = birth_span.text.strip()
                if "(" in text:
                    age_found = text.split("(")[-1].replace(")", "")
            
            # Ligue
            league_box = soup.find('span', class_='data-header__league')
            if league_box and league_box.find('a'):
                ligue_found = league_box.find('a').text.strip()

            # Stats (Matchs, Buts, Minutes)
            table = soup.find('table', class_='items')
            if table and table.find('tfoot'):
                cells = table.find('tfoot').find_all('td')
                try:
                    m_joues = cells[2].text.strip().replace('-', '0')
                    b = cells[3].text.strip().replace('-', '0')
                    mins = cells[-1].text.strip().replace('.', '').replace("'", "").replace('-', '0')
                except: pass

    except Exception as e:
        # print(f"Erreur : {e}")
        pass
    
    player_data['Position'] = pos_found
    player_data['Age'] = age_found
    player_data['Ligue'] = ligue_found
    player_data['Fin_Contrat'] = contrat_found
    player_data['Matchs_22_23'] = m_joues
    player_data['Buts_22_23'] = b
    player_data['Minutes_22_23'] = mins
    
    new_data.append(player_data)
    
    # Affichage de contrôle pour le premier joueur traité
    if index == 0:
        print(f"\n[TEST] Joueur: {nom} | Contrat trouvé: {contrat_found}")
        
    time.sleep(random.uniform(0.5, 1.2))

# 4. SAUVEGARDE
if new_data:
    df_newly_scraped = pd.DataFrame(new_data)
    df_final = pd.concat([df_existing, df_newly_scraped], ignore_index=True)
    df_final.to_csv(FILE_DATABASE, index=False)
    print(f"\n\n✅ SUCCÈS ! {len(df_newly_scraped)} joueurs ajoutés.")
    print(df_newly_scraped[['Nom', 'Fin_Contrat']].head())
else:
    print("\nAucune donnée récupérée.")