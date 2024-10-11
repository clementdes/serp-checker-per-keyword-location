import streamlit as st
import requests
import json
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime, timedelta
import hashlib
import pickle
import os

# Liste des villes
with open('villes.txt', 'r') as file:
    villes = [line.strip() for line in file]

# Initialisation de Streamlit
st.set_page_config(page_title="Multi Keyword + Location Google Search", layout="wide")

# Interface utilisateur
st.title("✨ Recherche Google par combinaisons mot-clé + localisation")

st.markdown(
    """
    <p>
        Créé par <a href="https://twitter.com/clementdesmouss" target="_blank">Clément Desmousseaux</a> |
        <a href="https://www.clement-desmousseaux.fr" target="_blank">Plus d'applications & scripts sur mon site web</a>
    """,
    unsafe_allow_html=True
)

st.divider()

# Dossier de cache
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Fonction pour obtenir le chemin de cache basé sur une clé unique
def get_cache_path(key):
    hash_key = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{hash_key}.pkl")

# Fonction pour lire le cache
def read_cache(key):
    path = get_cache_path(key)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            cache_data = pickle.load(f)
            if cache_data['expiry'] > datetime.now():
                return cache_data['data']
    return None

# Fonction pour écrire dans le cache
def write_cache(key, data, ttl=86400):
    path = get_cache_path(key)
    expiry = datetime.now() + timedelta(seconds=ttl)
    with open(path, 'wb') as f:
        pickle.dump({'data': data, 'expiry': expiry}, f)

# Fonction pour effacer le cache
def clear_cache():
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

# Bouton pour effacer le cache
if st.sidebar.button("Clear Cache"):
    clear_cache()
    st.sidebar.success("Cache effacé avec succès.")

# Demander à l'utilisateur de saisir le nom de domaine à vérifier
domain_name = st.text_input("Entrez le nom de domaine à vérifier (par exemple, 'example.com')")

# Demander à l'utilisateur de saisir jusqu'à 15 combinaisons mot-clé + localisation
combinations = []
for i in range(15):
    keyword = st.text_input(f"Entrez le mot-clé pour la combinaison {i + 1}")
    location = st.multiselect(f"Sélectionnez la localisation pour la combinaison {i + 1}", villes)
    if keyword and location:
        combinations.append((keyword, location[0]))

# Interface utilisateur pour la clé API
valueserp_api_key = st.sidebar.text_input("Entrez votre clé API ValueSERP", type="password")

# Fonction pour obtenir les résultats Google
def get_google_top_20(keyword, location, api_key):
    if not api_key:
        st.error("Clé API ValueSERP manquante.")
        return None

    # Générer une clé unique pour le cache
    cache_key = f"{keyword}_{location}_{api_key}"
    cached_results = read_cache(cache_key)
    if cached_results:
        return cached_results

    search_url = f"https://api.valueserp.com/search?api_key={api_key}&q={keyword}&location={location}&num=30"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        results = response.json().get('organic_results', [])
        write_cache(cache_key, results)
        return results
    except requests.RequestException as e:
        st.error(f"Erreur lors de la recherche avec ValueSERP : {e}")
        return None

# Bouton pour lancer la recherche de chaque combinaison
display_results = st.button("Rechercher toutes les combinaisons")

if display_results and combinations and valueserp_api_key:
    for keyword, location in combinations:
        st.subheader(f"Résultats pour : {keyword} - {location}")
        results = get_google_top_20(keyword, location, valueserp_api_key)
        if results:
            # Créer un DataFrame pour afficher les résultats dans un tableau
            data = {
                'Rank': [i + 1 for i in range(len(results[:20]))],
                'URL': [result['link'] for result in results[:20]],
                'Title': [result['title'] for result in results[:20]]
            }
            df = pd.DataFrame(data)
            st.table(df)

            # Vérifier la présence du nom de domaine fourni par l'utilisateur
            if domain_name:
                urls = [result['link'] for result in results]
                domain_present = False
                for i, url in enumerate(urls):
                    parsed_url = urlparse(url)
                    if domain_name in parsed_url.netloc:
                        st.write(f"Votre domaine apparaît en position #{i + 1} avec l'URL : {url}")
                        domain_present = True
                        break

                if not domain_present:
                    st.write(f"Le domaine ({domain_name}) n'a pas été trouvé dans le top 30 des résultats de Google.")
