import streamlit as st
import requests
import json
import pandas as pd
from urllib.parse import urlparse

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

# Demander à l'utilisateur de saisir jusqu'à 15 combinaisons mot-clé + localisation
combinations = []
for i in range(15):
    keyword = st.text_input(f"Entrez le mot-clé pour la combinaison {i + 1}")
    location = st.multiselect(f"Sélectionnez la localisation pour la combinaison {i + 1}", villes)
    if keyword and location:
        combinations.append((keyword, location[0]))

# Interface utilisateur pour la clé API et l'URL utilisateur
valueserp_api_key = st.sidebar.text_input("Entrez votre clé API ValueSERP", type="password")
user_url = st.text_input("Votre URL")

# Fonction pour obtenir les résultats Google
def get_google_top_20(keyword, location, api_key):
    if not api_key:
        st.error("Clé API ValueSERP manquante.")
        return None
    search_url = f"https://api.valueserp.com/search?api_key={api_key}&q={keyword}&location={location}&num=30"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        return response.json().get('organic_results', [])
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

            # Vérifier si l'URL de l'utilisateur est dans le top 30
            if user_url:
                urls = [result['link'] for result in results]
                parsed_user_url = urlparse(user_url)
                user_domain = parsed_user_url.netloc

                # Vérifier l'URL exacte
                if user_url in urls:
                    rank = urls.index(user_url) + 1
                    st.write(f"Votre URL est classée #{rank} dans les résultats de Google.")
                else:
                    st.write("Votre URL n'est pas dans le top 30 des résultats de Google.")

                # Vérifier la présence d'une autre URL du même domaine
                domain_present = False
                for i, url in enumerate(urls):
                    parsed_url = urlparse(url)
                    if parsed_url.netloc == user_domain:
                        st.write(f"Une autre URL du même domaine ({user_domain}) est classée #{i + 1}: {url}")
                        domain_present = True
                        break

                if not domain_present:
                    st.write(f"Aucune autre URL du même domaine ({user_domain}) n'a été trouvée dans le top 30 des résultats de Google.")
