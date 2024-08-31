
# Web Article Scraper

## Vue d'ensemble du projet

Ce projet est un scraper web conçu pour récupérer et extraire des articles de divers sites web. Le scraper peut naviguer sur les pages en utilisant différentes méthodes telles que la pagination, le défilement infini et les boutons "Charger plus". Il filtre ensuite les articles en fonction d'une date cible spécifiée et enregistre les résultats  dans des fichiers Excel individuels (un fichier par article) .

## Structure du projet

# Web Article Scraper

## Vue d'ensemble du projet

Ce projet est un scraper web conçu pour récupérer et extraire des articles de divers sites web. Le scraper peut naviguer sur les pages en utilisant différentes méthodes telles que la pagination, le défilement infini et les boutons "Charger plus". Il filtre ensuite les articles en fonction d'une date cible spécifiée et enregistre les résultats soit dans un fichier CSV unique (groupé par date), soit dans des fichiers Excel individuels (un fichier par article).

## Structure du projet

```bash
src/
│
├── utils.py            # Contient des fonctions utilitaires pour le scraping et le traitement des articles
├── scraper.py          # La logique principale du scraping incluant le support du multi-threading
└── main.py             # Le point d'entrée pour exécuter le scraper
Source/
└── source.csv          # Fichier de configuration contenant les sites web à scraper
Output/
    ├── per_date/     # Répertoire contenant les fichiers Excel individuels pour chaque article

```

## Fonctionnalités

- **Extraction de liens d'articles** : Le script extrait les liens des articles publiés sur une page web, en naviguant à travers la pagination, le défilement infini, ou le bouton "Load More".
  
- **Filtrage par Date** : Les articles sont filtrés en fonction de leur date de publication. Seuls les articles publiés à une date spécifique sont sauvegardés.

- **Sauvegarde des Articles** : Les articles filtrés peuvent être sauvegardés de la manière suivante:
  -  Tous les articles d'une même date sont regroupés dans un dossier.
  -  Chaque article est sauvegardé dans un fichier Excel individuel.

## Prérequis

- **Python 3.x** : Assurez-vous que Python 3.x est installé sur votre machine.
- **Dépendances Python** : Installez les bibliothèques Python nécessaires en exécutant la commande suivante :
    consulter le ficher -requirements.txt
  ```bash
  pip install requests beautifulsoup4 newspaper3k pandas python-dateutil selenium
  ```

- **Chromedriver** : Le script utilise Selenium pour contrôler un navigateur Chrome. Téléchargez [Chromedriver](https://sites.google.com/chromium.org/driver/) et assurez-vous que le chemin vers `chromedriver.exe` est correct dans le code.

## Configuration

### 1. **Fichier de Configuration CSV** :
   - Le fichier CSV contient la configuration pour les sites web à scraper, y compris les URL de base et les paramètres spécifiques comme le type de navigation (pagination, défilement infini, bouton "Load More"), ainsi que la balise HTML et la classe CSS contenant la date de publication.
   - La structure du fichier CSV doit être la suivante :



## Détails des paramètres

1. **`page_url`** :
   - **Description** : L'URL complète du site web que vous souhaitez scraper.
   - **Exemple** : `https://exemple.com/articles`

2. **`navigation_type`** :
   - **Description** : La méthode utilisée pour naviguer entre les pages du site web. Voici les options disponibles :
     - **`pagination`** : Navigation via des liens de page. 
     - **`infinite_scroll`** : Les nouvelles données se chargent automatiquement lorsque vous faites défiler la page vers le bas.
     - **`load_more_button`** : Les nouvelles données se chargent lorsque vous cliquez sur un bouton "Charger plus".

3. **`time_tag`** :
   - **Description** : La balise HTML qui contient la date de publication des articles.
   - **Exemple** : `time`, `span`

4. **`time_class`** :
   - **Description** : La classe CSS de la balise qui contient la date de publication.
   - **Exemple** : `entry-date published`, `post-date`
### 2. **Headers HTTP** :
   - Pour éviter les blocages, vous pouvez ajouter des headers HTTP (comme un user-agent) à vos requêtes.


## **Répartition des Fonctionnalités** :
### `utils.py`
 **extract_base_url(url)** :
   - Extrait l'URL de base à partir d'une URL complète.

 **read_config(file_path)** :
   - Lit un fichier CSV de configuration et retourne une liste de dictionnaires contenant les paramètres.

 **fetch_article_links(page_url, headers, target_date, navigation_type, time_tag, time_class)** :
   - Extrait les liens d'articles d'une page web, en naviguant via la pagination, le défilement infini, ou le bouton "Load More".

 **navigate_to_date_pagination(page_url, headers, target_date, time_tag, time_class, start_page)** :
   - Navigue à travers les pages d'un site en utilisant la pagination jusqu'à trouver des articles correspondant à la date cible.

 **navigate_to_date_infinite_scroll(page_url, headers, target_date, time_tag, time_class)** :
   - Utilise le défilement infini pour charger plus d'articles jusqu'à ce que la date cible soit trouvée.

**navigate_to_date_load_more(page_url, headers, target_date, time_tag, time_class)** :
   - Clique sur un bouton "Load More" pour charger plus d'articles jusqu'à ce que la date cible soit trouvée.

 **track_most_recent_date(soup, time_tag, time_class)** :
   - Suit la date la plus récente trouvée sur une page.

 **date_found_in_page(soup, target_date, time_tag, time_class)** :
   - Vérifie si la date cible est présente sur la page.

 **filter_and_scrape_articles(article_links, today)** :
   - Filtre les articles par date de publication et extrait leur contenu.

  **save_articles_per_date(results, target_date)** :
   - Sauvegarde les articles dans des fichiers CSV regroupés par date.

 **save_articles_per_article(results)** :
   - Sauvegarde chaque article dans un fichier Excel individuel.
### `scraper.py`

 **run_scraper** :
 - Orchestre l'ensemble du processus de scraping. Il charge la configuration, récupère les liens des articles de manière concurrente, filtre et extrait les articles, puis enregistre les résultats.

### `main.py`
  **main** :
 - Le point d'entrée du scraper. Il appelle simplement `run_scraper()` pour démarrer le processus de scraping.
