import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# On prépare une liste pour tout stocker
all_transfers = []

# Nombre de pages à scraper
nombre_de_pages = 20

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Démarrage du scraping sur {nombre_de_pages} pages...")

for page in range(1, nombre_de_pages + 1):
    url = f"https://www.transfermarkt.fr/transfers/saisontransfers/statistik/top/plus/0/galerie/0?saison_id=2023&transferfenster=alle&land_id=&ausrichtung=&spielerposition_id=&altersklasse=&leihe=&page={page}"
    
    print(f"Scraping page {page}...", end=" ")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='items')
            
            if not table:
                print("Tableau non trouvé.")
                continue
                
            rows = table.find('tbody').find_all('tr')
            
            joueurs_trouves = 0
            
            for row in rows:
                try:
                    # SÉCURITÉ 1 : Vérifier qu'on a bien des cellules
                    cells = row.find_all('td')
                    if len(cells) < 5:  # Si la ligne a moins de 5 colonnes, c'est une ligne de séparation (headers), on saute
                        continue

                    # 1. Nom et Lien
                    # Parfois le lien est dans la 1ère colonne, parfois la 2ème (numéro de maillot)
                    # On cherche la classe 'hauptlink' qui contient le lien vers le joueur
                    name_tag = row.find('td', class_='hauptlink').find('a')
                    if not name_tag:
                        continue
                        
                    name = name_tag.text.strip()
                    player_url = "https://www.transfermarkt.fr" + name_tag['href']
                    
                    # 2. Âge (Index 2 normalement, mais sécurisons)
                    age = cells[2].text.strip()
                    
                    # 3. Nationalité
                    nationality = "Inconnu"
                    # On cherche l'image du drapeau
                    flags = row.find_all('img', class_='flaggenrahmen')
                    if len(flags) > 0:
                        nationality = flags[0]['title']
                    else:
                        # Fallback
                        try:
                            if cells[3].find('img'):
                                nationality = cells[3].find('img')['title']
                        except:
                            pass

                    # 4. Prix (Target)
                    fee_tag = row.find('td', class_='rechts hauptlink')
                    if not fee_tag:
                        continue
                    
                    fee = fee_tag.text.strip()
                    
                    # On ignore les prêts ou montants inconnus
                    if "Prêt" in fee or "?" in fee or "-" in fee:
                        continue

                    all_transfers.append({
                        'Nom': name,
                        'Age': age,
                        'Nationalite': nationality,
                        'Prix_Raw': fee,
                        'URL_Profil': player_url
                    })
                    joueurs_trouves += 1
                    
                except Exception as e:
                    # Si une ligne plante, on l'affiche mais ON CONTINUE les autres lignes
                    # print(f"Erreur ligne: {e}") 
                    continue
            
            print(f"-> OK ({joueurs_trouves} joueurs)")
            
        else:
            print(f"Erreur HTTP : {response.status_code}")
            
    except Exception as e:
        print(f"Crash Page : {e}")

    # PAUSE
    time.sleep(random.uniform(2, 4))

# Création du CSV Final
df = pd.DataFrame(all_transfers)
print(f"\nTerminé ! {len(df)} joueurs récupérés.")

# Sauvegarde
df.to_csv('data/raw/transfers_large_dataset_.csv', index=False)