# ============================================
# bluesky_scraper.py - VERSION SDK officiel
# ============================================
from atproto import Client
from pymongo import MongoClient
from datetime import datetime
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGO_URL, MONGO_DB, COLLECTION_RAW, KEYWORDS
from config.settings import BLUESKY_USERNAME, BLUESKY_PASSWORD


def sauvegarder_dans_mongodb(posts, mot_cle):
    client_mongo = MongoClient(MONGO_URL)
    db = client_mongo[MONGO_DB]
    collection = db[COLLECTION_RAW]
    nb_inseres = 0
    for post in posts:
        doc = {
            "uri":            post.uri,
            "texte":          post.record.text,
            "auteur":         post.author.handle,
            "date":           post.indexed_at,
            "_mot_cle":       mot_cle,
            "_date_collecte": datetime.now().isoformat()
        }
        resultat = collection.update_one(
            {"uri": doc["uri"]},
            {"$set": doc},
            upsert=True
        )
        if resultat.upserted_id:
            nb_inseres += 1
    client_mongo.close()
    return nb_inseres


def lancer_collecte():
    print("=== Démarrage de la collecte Bluesky ===\n")

    # Connexion avec le SDK officiel
    client = Client()
    client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)
    print("✅ Connecté à Bluesky\n")

    total = 0
    for mot in KEYWORDS:
        print(f"🔍 Recherche : '{mot}'...")
        reponse = client.app.bsky.feed.search_posts({"q": mot, "limit": 50})
        posts = reponse.posts
        nb = sauvegarder_dans_mongodb(posts, mot)
        print(f"   ✅ {len(posts)} posts trouvés, {nb} nouveaux sauvegardés\n")
        total += nb

    print(f"=== Collecte terminée : {total} nouveaux posts au total ===")


if __name__ == "__main__":
    lancer_collecte()