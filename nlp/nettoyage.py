# ============================================
# nettoyage.py 
# ============================================
import re
import os
import sys
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGO_URL, MONGO_DB, COLLECTION_RAW, COLLECTION_CLEAN


def nettoyer_texte(texte):
    if not texte:
        return ""
    texte = re.sub(r"http\S+|www\S+", "", texte)
    texte = re.sub(r"@\w+", "", texte)
    texte = re.sub(r"#\w+", "", texte)
    texte = re.sub(r"[^a-zA-Z0-9\sàâäéèêëîïôùûüç]", "", texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    texte = texte.lower()
    return texte


def extraire_texte(post):
    """
    Essaie plusieurs chemins possibles pour trouver le texte.
    """
    # Chemin direct (notre scraper corrigé)
    if post.get("texte"):
        return post["texte"]

    # Chemin imbriqué ancienne version
    try:
        return post["record"]["text"]
    except (KeyError, TypeError):
        pass

    # Autres chemins possibles
    for champ in ["text", "content", "body"]:
        if post.get(champ):
            return post[champ]

    return ""


def traiter_tous_les_posts():
    client = MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    collection_brute = db[COLLECTION_RAW]
    collection_propre = db[COLLECTION_CLEAN]

    print("=== Démarrage du nettoyage NLP ===\n")

    posts_bruts = list(collection_brute.find({}))
    print(f"📦 {len(posts_bruts)} posts bruts à traiter...\n")

    nb_traites = 0
    nb_ignores = 0

    for post in posts_bruts:
        texte_brut = extraire_texte(post)
        texte_propre = nettoyer_texte(texte_brut)

        if len(texte_propre) < 10:
            nb_ignores += 1
            continue

        post_propre = {
            "uri":             post.get("uri", ""),
            "texte_brut":      texte_brut,
            "texte_propre":    texte_propre,
            "auteur":          post.get("auteur", post.get("author", {}).get("handle", "inconnu")),
            "date":            post.get("date", post.get("indexedAt", "")),
            "mot_cle":         post.get("_mot_cle", ""),
            "date_traitement": __import__("datetime").datetime.now().isoformat()
        }

        collection_propre.update_one(
            {"uri": post_propre["uri"]},
            {"$set": post_propre},
            upsert=True
        )
        nb_traites += 1

    client.close()
    print(f"✅ {nb_traites} posts nettoyés et sauvegardés")
    print(f"⏭️  {nb_ignores} posts ignorés (trop courts)")


if __name__ == "__main__":
    traiter_tous_les_posts()