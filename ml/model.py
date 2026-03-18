# ============================================
# modele.py - Entraînement K-Means
# ============================================
# K-Means regroupe les posts en clusters (groupes).
# On interprète ensuite chaque groupe :
#   Cluster 0 → posts probablement fiables
#   Cluster 1 → posts suspects / à vérifier
#   Cluster 2 → posts clairement faux / désinformation

import os
import sys
import joblib
import numpy as np
from sklearn.cluster import KMeans

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import NB_CLUSTERS
from vectorisation import vectoriser


def entrainer_modele():
    """
    Entraîne un modèle K-Means sur les textes vectorisés.
    """
    print("=== Entraînement du modèle K-Means ===\n")

    # Étape 1 : Vectorisation
    matrice, uris, _ = vectoriser()

    # Étape 2 : Entraînement K-Means
    print(f"\n🤖 Entraînement K-Means avec {NB_CLUSTERS} clusters...")
    modele = KMeans(
        n_clusters=NB_CLUSTERS,
        random_state=42,      # Pour avoir des résultats reproductibles
        n_init=10             # Nombre d'initialisations (garde le meilleur)
    )
    modele.fit(matrice)

    # Étape 3 : Affichage des résultats
    labels = modele.labels_
    for i in range(NB_CLUSTERS):
        nb = np.sum(labels == i)
        print(f"   Cluster {i} : {nb} posts ({nb/len(labels)*100:.1f}%)")

    # Étape 4 : Sauvegarde du modèle
    joblib.dump(modele, "models/modele_kmeans.pkl")
    print("\n💾 Modèle sauvegardé dans models/modele_kmeans.pkl")

    return modele, labels, uris


def predire(texte_propre):
    """
    Prédit le cluster d'un nouveau texte.
    Retourne un entier (0, 1 ou 2).
    """
    vectoriseur = joblib.load("models/vectoriseur_tfidf.pkl")
    modele      = joblib.load("models/modele_kmeans.pkl")

    vecteur = vectoriseur.transform([texte_propre])
    cluster = modele.predict(vecteur)[0]
    return int(cluster)


if __name__ == "__main__":
    entrainer_modele()