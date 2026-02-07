import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# On prépare une liste pour tout stocker
all_transfers = []

# Nombre de pages à scraper
nombre_de_pages = 5 

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Démarrage du scraping sur {nombre_de_pages} pages...")

for page in range(1, nombre_de_pages + 1):
    # L'URL change à chaque tour de boucle grâce à la variable {page}
    # On prend 'saisontransfers' qui liste tout, pas juste le top
    url = f"https://www.transfermarkt.fr/transfers/saisontransfers/statistik/top/plus/0/galerie/0?saison_id=2023&transferfenster=alle&land_id=&ausrichtung=&spielerposition_id=&altersklasse=&leihe=&page={page}"
    
    print(f"Scraping page {page}...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='items')
            
            # Si pas de tableau, on arrête (fin des pages)
            if not table:
                print("Fin des données trouvée.")
                break
                
            rows = table.find('tbody').find_all('tr')
            
            for row in rows:
                try:
                    # 1. Nom et Lien vers le profil (Important pour la suite !)
                    name_tag = row.find('td', class_='hauptlink')
                    if not name_tag or not name_tag.find('a'):
                        continue
                        
                    name_tag_a = name_tag.find('a')
                    name = name_tag_a.text.strip()
                    player_url = "https://www.transfermarkt.fr" + name_tag_a['href'] # On garde le lien pour plus tard
                    
                    # 2. Âge
                    cells = row.find_all('td')
                    if len(cells) < 4:  # On a besoin d'au moins 4 cellules
                        continue
                    age = cells[2].text.strip()
                    
                    # 3. Nationalité 
                    # On essaie de choper le titre de l'image du drapeau
                    try:
                        nat_img = cells[3].find('img')
                        nationality = nat_img['title'] if nat_img else "Inconnu"
                    except:
                        nationality = "Inconnu"

                    # 4. Prix (Target)
                    fee_tag = row.find('td', class_='rechts hauptlink')
                    if not fee_tag:
                        continue
                    # Lien vers le détail du transfert
                    fee = fee_tag.text.strip()
                    
                    # On ignore les prêts pour l'instant (souvent marqués par "Prêt" ou des montants bizarres)
                    if "Prêt" in fee or "?" in fee:
                        continue

                    all_transfers.append({
                        'Nom': name,
                        'Age': age,
                        'Nationalite': nationality,
                        'Prix_Raw': fee,
                        'URL_Profil': player_url  # Très important : on garde l'adresse de sa fiche !
                    })
                    
                except AttributeError:
                    continue
        else:
            print(f"Erreur page {page} : {response.status_code}")
            
    except Exception as e:
        print(f"Problème technique : {e}")

    # PAUSE OBLIGATOIRE pour ne pas surcharger le serveur et éviter d'être bloqué
    time.sleep(random.uniform(2, 5))

# Création du CSV Final
df = pd.DataFrame(all_transfers)
print(f"\nTerminé ! {len(df)} joueurs récupérés.")
print(df.tail()) # Affiche les derniers (les moins chers)

# Sauvegarde
df.to_csv('data/raw/transfers_large_dataset.csv', index=False)