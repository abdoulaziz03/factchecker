# ============================================
# vectorisation.py - TF-IDF
# ============================================
# Transforme les textes en vecteurs numériques
# grâce à l'algorithme TF-IDF.
#
# TF-IDF = Term Frequency - Inverse Document Frequency
# → Un mot fréquent dans UN post mais rare dans les
#   autres aura un score élevé (= mot important)

import os
import sys
import joblib
import pandas as pd
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGO_URL, MONGO_DB, COLLECTION_CLEAN, MAX_FEATURES


def vectoriser():
    """
    Charge les textes propres, les vectorise avec TF-IDF,
    et sauvegarde le vectoriseur entraîné.
    """
    client = MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    posts = list(db[COLLECTION_CLEAN].find({}, {"texte_propre": 1, "uri": 1}))
    client.close()

    print(f"📊 {len(posts)} posts chargés pour la vectorisation")

    textes = [p["texte_propre"] for p in posts]
    uris   = [p["uri"] for p in posts]

    # Création du vectoriseur TF-IDF
    vectoriseur = TfidfVectorizer(
        max_features=MAX_FEATURES,   # Garde les N mots les plus importants
        min_df=2,                    # Ignore les mots qui apparaissent < 2 fois
        ngram_range=(1, 2),          # Prend les mots seuls ET les paires de mots
        stop_words=None              # On garde tous les mots (déjà nettoyé)
    )

    # Entraînement + transformation
    matrice = vectoriseur.fit_transform(textes)
    print(f"✅ Matrice TF-IDF créée : {matrice.shape[0]} posts × {matrice.shape[1]} mots")

    # Sauvegarde du vectoriseur (pour pouvoir l'utiliser dans l'API)
    os.makedirs("models", exist_ok=True)
    joblib.dump(vectoriseur, "models/vectoriseur_tfidf.pkl")
    print("💾 Vectoriseur sauvegardé dans models/vectoriseur_tfidf.pkl")

    return matrice, uris, vectoriseur


if __name__ == "__main__":
    vectoriser()