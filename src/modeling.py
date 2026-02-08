import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import os

# --- 1. CHARGEMENT INTELLIGENT ---
possibilities = [
    'data/processed/transfers_ready_for_model.csv',
    '../data/processed/transfers_ready_for_model.csv'
]
file_path = None
for path in possibilities:
    if os.path.exists(path):
        file_path = path
        break

if not file_path:
    print("❌ Fichier introuvable. Lance le Script 3 (Nettoyage) d'abord.")
    exit()

df = pd.read_csv(file_path)

# --- SÉCURITÉ ANTI-PLANTAGE ---
# On vire les lignes qui ont des trous (ex: João Félix qui n'a pas de valeur marchande)
print(f"Joueurs au départ : {len(df)}")
df = df.dropna(subset=['Valeur_Marchande_Clean', 'Prix', 'Duree_Contrat'])
print(f"Joueurs après nettoyage de sécurité : {len(df)}")

# --- 2. DÉFINITION DES FEATURES ---
# On liste explicitement ce qu'on veut
features = [
    'Age', 
    'Position_Encoded', 
    'Valeur_Marchande_Clean',
    'Matchs_22_23', 
    'Buts_22_23', 
    'Minutes_22_23',
    'Duree_Contrat'  # <-- Elle est bien là maintenant !
]

# On ajoute automatiquement toutes les colonnes de Ligues
ligue_cols = [c for c in df.columns if 'Ligue_' in c]
features.extend(ligue_cols)

print(f"\n--- DÉMARRAGE DU MODÈLE ---")
print(f"Variables utilisées ({len(features)}) : {features}")

# 3. PRÉPARATION
X = df[features]
y = df['Prix']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. ENTRAÎNEMENT
model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

# 5. RÉSULTATS
predictions = model.predict(X_test)
r2 = r2_score(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)

print(f"\n📈 RÉSULTATS FINAUX :")
print(f"  > R² (Précision) : {r2:.4f} / 1.00")
print(f"  > Erreur Moyenne : {mae:,.0f} €")

# 6. IMPORTANCE DES VARIABLES
importances = pd.DataFrame({'feature': features, 'importance': model.feature_importances_})
print("\n--- CE QUI COMPTE POUR LE PRIX ---")
print(importances.sort_values('importance', ascending=False).head(10))

# 7. GRAPHIQUE
try:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_test, y=predictions, alpha=0.6, color='#4c72b0', edgecolor='k')
    
    # Ligne rouge parfaite
    min_val = min(y_test.min(), predictions.min())
    max_val = max(y_test.max(), predictions.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Prédiction Parfaite')
    
    plt.xlabel('Prix RÉEL')
    plt.ylabel('Prix PRÉDIT par IA')
    plt.title(f'Précision du Modèle (R²={r2:.2f})')
    plt.legend()
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    
    plt.savefig('resultats_final.png')
    print("\n🖼️ Graphique sauvegardé : resultats_final.png")
    # plt.show() # Décommenter si tu n'es pas dans un terminal pur
except Exception as e:
    print(f"Pas de graphique possible (pas grave) : {e}")

print("\n--- 🕵️‍♂️ LE RADAR À PÉPITES ---")

# On crée un tableau avec les résultats
resultats = X_test.copy()
resultats['Prix_Reel'] = y_test
resultats['Prix_IA'] = predictions
resultats['Nom'] = df.loc[resultats.index, 'Nom'] # On récupère les noms

# Calcul de l'écart (Positif = Bonne affaire, Négatif = Surpayé)
# Exemple : IA dit 25M, Payé 15M -> Ecart = +10M (Super affaire !)
resultats['Ecart_Mio'] = (resultats['Prix_IA'] - resultats['Prix_Reel']) / 1_000_000

# Top 5 des Bonnes Affaires (Sous-payés)
bonnes_affaires = resultats.sort_values('Ecart_Mio', ascending=False).head(5)

print("\n💎 TOP 5 - LES BONNES AFFAIRES (Joueurs achetés moins cher que leur valeur réelle) :")
for i, row in bonnes_affaires.iterrows():
    print(f"✅ {row['Nom']}")
    print(f"   - Payé : {row['Prix_Reel']/1e6:.1f} M€")
    print(f"   - Valeur IA : {row['Prix_IA']/1e6:.1f} M€")
    print(f"   - Gain potentiel : +{row['Ecart_Mio']:.1f} M€")
    print(f"   - Pourquoi ? Contrat: {row['Duree_Contrat']} ans, Age: {row['Age']}")

# Top 5 des Surpayés (Arnaques ?)
surpayes = resultats.sort_values('Ecart_Mio', ascending=True).head(5)

print("\n💸 TOP 5 - LES JOUEURS SURPAYÉS  :")
for i, row in surpayes.iterrows():
    print(f"⚠️ {row['Nom']}")
    print(f"   - Payé : {row['Prix_Reel']/1e6:.1f} M€")
    print(f"   - Valeur IA : {row['Prix_IA']/1e6:.1f} M€")
    print(f"   - Perte estimée : {row['Ecart_Mio']:.1f} M€")