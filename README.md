# 🔍 FactChecker Bluesky

> Application de vérification d'informations en temps réel, propulsée par l'IA et les données de Bluesky.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30-red?logo=streamlit)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb)](https://mongodb.com)
[![Airflow](https://img.shields.io/badge/Airflow-2.8-blue?logo=apacheairflow)](https://airflow.apache.org)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-purple?logo=railway)](https://railway.app)

---

## 🌐 Démo en ligne

| Service | URL |
|---|---|
| 🎯 Dashboard | [factchecker.streamlit.app](https://factchecker-gmrtkha22gxd8pmrkcphxi.streamlit.app) |
| ⚡ API REST | [factchecker.railway.app](https://factchecker-production-310f.up.railway.app) |
| 📖 API Docs | [/docs](https://factchecker-production-310f.up.railway.app/docs) |

---

## 📸 Aperçu

### Dashboard
![Dashboard](image/dashboard1.png)

### Pipeline Airflow
![Airflow](image/airflow.png)

### Base de données MongoDB
![MongoDB](image/mongodb.png)

---

## 🚀 Fonctionnalités

- 🤖 **Analyse IA** — Vérification instantanée avec LLaMA 3.3 (Groq)
- 🌐 **Recherche web** — Sources DuckDuckGo en temps réel
- ✅ **Fact-checkers officiels** — Snopes, AFP Factuel, Les Décodeurs, Checknews
- 📖 **Wikipedia** — Vérification sur les faits encyclopédiques
- 🌍 **Multilingue** — Détection automatique de la langue (FR, EN, etc.)
- 📊 **Score de confiance** — Calculé selon le nombre et la qualité des sources
- ⚡ **Cache intelligent** — Réponses instantanées pour les textes déjà analysés
- 👤 **Comptes utilisateurs** — Inscription / connexion sécurisée (bcrypt)
- 📜 **Historique personnel** — Suivi de toutes tes analyses
- 🔄 **Collecte automatique** — Pipeline Airflow toutes les heures

---

## 🏗️ Architecture
```
factchecker/
│
├── collecte/           ← Collecte des posts Bluesky (API atproto)
├── nlp/                ← Nettoyage et traitement du texte
├── ml/                 ← Vectorisation TF-IDF + modèle K-Means
├── api/                ← API REST FastAPI
├── dashboard/          ← Interface Streamlit
├── dags/               ← Pipeline Airflow (orchestration)
├── config/             ← Configuration globale
└── docker-compose.yml  ← Airflow + PostgreSQL
```

## 🔄 Pipeline de données
```
Bluesky API
    ↓
MongoDB (données brutes)
    ↓
NLP (nettoyage, tokenisation)
    ↓
MongoDB (données propres)
    ↓
TF-IDF + K-Means
    ↓
Modèle ML (.pkl)
    ↓
FastAPI ←→ Groq LLaMA 3.3
    ↓
Streamlit Dashboard
```

---

## 🛠️ Stack technique

| Composant | Technologie |
|---|---|
| Collecte | atproto SDK (Bluesky) |
| NLP | Python / regex / langdetect |
| ML | scikit-learn (TF-IDF + K-Means) |
| IA | Groq / LLaMA 3.3 70B |
| Recherche web | DuckDuckGo Search |
| Base de données | MongoDB Atlas + Railway |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit |
| Authentification | bcrypt |
| Orchestration | Apache Airflow 2.8 |
| Conteneurisation | Docker + Docker Compose |
| Déploiement API | Railway |
| Déploiement Dashboard | Streamlit Cloud |

---

## ⚙️ Installation locale

### Prérequis
- Python 3.11+
- MongoDB (local ou Atlas)
- Docker Desktop (pour Airflow)

### 1. Clone le repo
```bash
git clone https://github.com/abdoulaziz03/factchecker.git
cd factchecker
```

### 2. Installe les dépendances
```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_sm
```

### 3. Configure les variables d'environnement
Crée un fichier `.env` :
```env
MONGO_URL=mongodb://localhost:27017
BLUESKY_USERNAME=ton-pseudo.bsky.social
BLUESKY_PASSWORD=ton-app-password
GROQ_API_KEY=gsk_...
```

### 4. Lance le pipeline
```bash
# Collecte des posts
python collecte/bluesky_scraper.py

# Nettoyage NLP
python nlp/nettoyage.py

# Entraînement ML
python ml/modele.py

# Lance l'API
python api/main.py

# Lance le dashboard (nouveau terminal)
streamlit run dashboard/app.py
```

### 5. Lance Airflow (Docker)
```bash
docker compose up -d
# Interface : http://localhost:8080
# Login : admin / admin
```

---

## 📡 API Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Statut de l'API |
| POST | `/verifier` | Analyse une information |
| POST | `/inscription` | Créer un compte |
| POST | `/connexion` | Se connecter |
| GET | `/historique` | Récupérer l'historique |

### Exemple d'utilisation
```bash
curl -X POST "https://factchecker-production-310f.up.railway.app/verifier" \
  -H "Content-Type: application/json" \
  -d '{"texte": "La terre est plate", "utilisateur": "test"}'
```

### Réponse
```json
{
  "texte_original": "La terre est plate",
  "verdict": "Probablement faux",
  "explication": "Les sources scientifiques et Wikipedia confirment que la Terre est sphérique.",
  "score_fiabilite": 0.20,
  "couleur": "rouge",
  "langue": "fr",
  "nb_sources": 8,
  "depuis_cache": false
}
```

---

## 🔐 Sécurité

- Mots de passe hashés avec **bcrypt**
- Variables sensibles dans `.env` (jamais commitées)
- Protection GitHub contre les secrets exposés
- Analyse sans compte possible, historique réservé aux membres

---

## 📈 Améliorations futures

- [ ] Extension Chrome pour analyser directement sur le web
- [ ] Graphiques et statistiques avancées
- [ ] Notification par email pour les fausses infos détectées
- [ ] Support de l'analyse d'images (deepfakes)
- [ ] API publique avec rate limiting

---

## 👨‍💻 Auteur

**Abdoulaziz** — [@abdoulaziz03](https://github.com/abdoulaziz03)

---

## 📄 Licence

MIT License — libre d'utilisation et de modification.