import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# --- CONFIGURATION ---
NOMBRE_PAGES = 74
SAISON = 2023

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

all_transfers = []
print(f"--- DÉMARRAGE DU SCRAPING (Liste des transferts) ---")

for page in range(74, NOMBRE_PAGES + 1):
    url = f"https://www.transfermarkt.fr/transfers/saisontransfers/statistik/top/plus/1/galerie/0?saison_id={SAISON}&transferfenster=alle&land_id=&ausrichtung=&spielerposition_id=&altersklasse=&leihe=&page={page}"
    
    print(f"Lecture page {page}/{NOMBRE_PAGES}...", end="\r")
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', class_='items')
        if not table:
            continue
        
        # On ne prend que les lignes de joueurs (odd/even) pour éviter les titres
        rows = table.find('tbody').find_all('tr', class_=['odd', 'even'])
        
        for row in rows:
            try:
                # 1. NOM & URL
                name_tag = row.find('td', class_='hauptlink').find('a')
                if not name_tag: continue
                name = name_tag.text.strip()
                url_profil = "https://www.transfermarkt.fr" + name_tag['href']

                # Sécurité Club (Si le lien ne contient pas 'spieler', ce n'est pas un joueur)
                if "/profil/spieler/" not in url_profil:
                    continue

                # 2. AGE (Correction Positionnelle)
                # On récupère TOUTES les cellules centrées de la ligne
                centered_cells = row.find_all('td', class_='zentriert')
                
                # Structure standard Transfermarkt : [0]=Rang, [1]=Age, [2]=Nat...
                age = "Inconnu"
                if len(centered_cells) >= 2:
                    age = centered_cells[1].text.strip()
                else:
                    # Cas rare où la structure change
                    continue

                # 3. NATIONALITÉ
                nat_img = row.find('img', class_='flaggenrahmen')
                nality = nat_img['title'] if nat_img else "Inconnu"

                # 4. VALEUR MARCHANDE & PRIX
                rechts_cells = row.find_all('td', class_='rechts')
                vals = [c.text.strip() for c in rechts_cells if any(x in c.text for x in ['€', '?', '-'])]
                
                market_val = "Inconnu"
                fee = "Inconnu"
                
                if len(vals) >= 2:
                    market_val = vals[-2]
                    fee = vals[-1]
                elif len(vals) == 1:
                    fee = vals[0]

                # Filtre Prêt
                if "Prêt" in fee or "prêt" in fee.lower():
                    continue

                all_transfers.append({
                    'Nom': name,
                    'Age': age,
                    'Nationalite': nality,
                    'Valeur_Marchande': market_val,
                    'Prix_Raw': fee,
                    'URL_Profil': url_profil
                })
                
            except Exception:
                continue
                
    except Exception as e:
        print(f"Erreur page {page}: {e}")

    time.sleep(random.uniform(1, 2))

# Sauvegarde
df = pd.DataFrame(all_transfers)
df = df.drop_duplicates(subset=['URL_Profil'])

print(f"\n✅ TERMINÉ ! {len(df)} joueurs récupérés.")
print(df[['Nom', 'Age', 'Prix_Raw']].head(15)) # Affiche les 15 premiers pour vérifier 
df.to_csv('data/raw/transfers_large_dataset2.csv', index=False)