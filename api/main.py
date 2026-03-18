import os
import sys
import json
import re
import bcrypt
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from ddgs import DDGS
from dotenv import load_dotenv

try:
    from langdetect import detect
except:
    detect = lambda x: "fr"

try:
    from deep_translator import GoogleTranslator
except:
    GoogleTranslator = None

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client_groq = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="FactChecker API", version="5.0.0")


class TexteEntrant(BaseModel):
    texte: str
    utilisateur: str = "anonyme"


class Utilisateur(BaseModel):
    pseudo: str
    mot_de_passe: str


def get_mongo():
    from pymongo import MongoClient
    MONGO_URL = os.environ.get("MONGO_URL", "")
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000, tlsInsecure=True)


@app.get("/")
def accueil():
    return {"message": "FactChecker API en ligne ✅"}


@app.post("/inscription")
def inscription(user: Utilisateur):
    try:
        client = get_mongo()
        db = client["factchecker"]
        if db["utilisateurs"].find_one({"pseudo": user.pseudo}):
            client.close()
            return {"succes": False, "message": "Ce pseudo est déjà pris"}
        mot_de_passe_hash = bcrypt.hashpw(
            user.mot_de_passe.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        db["utilisateurs"].insert_one({
            "pseudo":           user.pseudo,
            "mot_de_passe":     mot_de_passe_hash,
            "date_inscription": datetime.now().isoformat()
        })
        client.close()
        return {"succes": True, "message": f"Compte créé pour {user.pseudo} !"}
    except Exception as e:
        return {"succes": False, "message": str(e)}


@app.post("/connexion")
def connexion(user: Utilisateur):
    try:
        client = get_mongo()
        db = client["factchecker"]
        utilisateur = db["utilisateurs"].find_one({"pseudo": user.pseudo})
        client.close()
        if not utilisateur:
            return {"succes": False, "message": "Pseudo introuvable"}
        if bcrypt.checkpw(
            user.mot_de_passe.encode("utf-8"),
            utilisateur["mot_de_passe"].encode("utf-8")
        ):
            return {"succes": True, "message": f"Bienvenue {user.pseudo} !"}
        return {"succes": False, "message": "Mot de passe incorrect"}
    except Exception as e:
        return {"succes": False, "message": str(e)}


@app.get("/historique")
def get_historique(utilisateur: str = None):
    try:
        client = get_mongo()
        db = client["factchecker"]
        filtre = {"utilisateur": utilisateur} if utilisateur else {}
        historique = list(db["historique"].find(filtre, {"_id": 0}).sort("date", -1).limit(50))
        client.close()
        return historique
    except Exception as e:
        print(f"MongoDB : {e}")
        return []


def detecter_langue(texte):
    """Détecte la langue du texte."""
    try:
        return detect(texte)
    except:
        return "fr"


def traduire_en_anglais(texte):
    """Traduit le texte en anglais si nécessaire."""
    try:
        if GoogleTranslator:
            return GoogleTranslator(source="auto", target="en").translate(texte)
    except:
        pass
    return texte


def rechercher_sources(texte, nb=5):
    """Recherche des articles via DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            resultats = list(ddgs.text(texte, max_results=nb))
        return [{
            "titre":   r.get("title", ""),
            "url":     r.get("href", ""),
            "extrait": r.get("body", "")[:300]
        } for r in resultats]
    except Exception as e:
        print(f"Erreur recherche web : {e}")
        return []


def rechercher_fact_checkers(texte_anglais):
    """Recherche sur des sites de fact-checking connus."""
    sources_fc = []
    sites = [
        "site:snopes.com",
        "site:factcheck.org",
        "site:afp.com/fr/agence/sections-afp/factuel",
        "site:lemonde.fr/les-decodeurs",
        "site:liberation.fr/checknews"
    ]
    try:
        with DDGS() as ddgs:
            for site in sites[:3]:
                resultats = list(ddgs.text(f"{texte_anglais} {site}", max_results=1))
                for r in resultats:
                    sources_fc.append({
                        "titre":   r.get("title", ""),
                        "url":     r.get("href", ""),
                        "extrait": r.get("body", "")[:300],
                        "type":    "fact-checker"
                    })
    except Exception as e:
        print(f"Erreur fact-checkers : {e}")
    return sources_fc


def calculer_score_confiance(sources, verdict):
    """
    Calcule un score de confiance basé sur :
    - Le nombre de sources trouvées
    - La présence de sites fact-checkers reconnus
    - La cohérence du verdict
    """
    score_base = {
        "Fiable": 0.75,
        "À vérifier": 0.50,
        "Probablement faux": 0.20
    }.get(verdict, 0.50)

    # Bonus selon le nombre de sources
    nb_sources = len(sources)
    if nb_sources >= 4:
        bonus_sources = 0.10
    elif nb_sources >= 2:
        bonus_sources = 0.05
    else:
        bonus_sources = 0.0

    # Bonus si sources fact-checkers présentes
    fc_sites = ["snopes", "factcheck", "afp", "decodeurs", "checknews", "lemonde", "liberation"]
    nb_fc = sum(1 for s in sources if any(fc in s.get("url", "").lower() for fc in fc_sites))
    bonus_fc = min(nb_fc * 0.05, 0.15)

    score_final = min(score_base + bonus_sources + bonus_fc, 0.99)
    return round(score_final, 2)


@app.post("/verifier")
def verifier_information(entree: TexteEntrant):
    try:
        # Détection de la langue
        langue = detecter_langue(entree.texte)
        texte_anglais = traduire_en_anglais(entree.texte) if langue != "en" else entree.texte

        # Recherche sources générales + fact-checkers
        sources          = rechercher_sources(entree.texte, nb=4)
        sources_fc       = rechercher_fact_checkers(texte_anglais)
        toutes_sources   = sources + sources_fc

        contexte_sources = "\n".join(
            [f"- [{s.get('type','web')}] {s['titre']} : {s['extrait']}" for s in toutes_sources]
        ) if toutes_sources else "Aucune source trouvée."

        prompt = f"""Tu es un expert en fact-checking international. Analyse cette affirmation en tenant compte des sources trouvées.
Réponds UNIQUEMENT en JSON valide, sans texte avant ou après.

Affirmation : "{entree.texte}"
Langue détectée : {langue}

Sources trouvées (web + fact-checkers) :
{contexte_sources}

Réponds avec ce format JSON exact :
{{
  "verdict": "Fiable" ou "À vérifier" ou "Probablement faux",
  "score": 0.8,
  "couleur": "vert" ou "orange" ou "rouge",
  "explication": "Une phrase expliquant pourquoi en citant les sources",
  "langue": "{langue}"
}}"""

        reponse = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400
        )

        contenu = reponse.choices[0].message.content
        match   = re.search(r'\{.*\}', contenu, re.DOTALL)
        resultat = json.loads(match.group())

        # Score de confiance précis
        score_confiance = calculer_score_confiance(toutes_sources, resultat["verdict"])

        # Sauvegarde MongoDB
        try:
            client = get_mongo()
            db = client["factchecker"]
            db["historique"].insert_one({
                "texte":          entree.texte,
                "utilisateur":    entree.utilisateur,
                "verdict":        resultat["verdict"],
                "explication":    resultat["explication"],
                "score":          score_confiance,
                "couleur":        resultat["couleur"],
                "langue":         langue,
                "sources":        toutes_sources,
                "nb_sources":     len(toutes_sources),
                "nb_fc":          len(sources_fc),
                "date":           datetime.now().isoformat()
            })
            client.close()
        except Exception as mongo_err:
            print(f"MongoDB : {mongo_err}")

        return {
            "texte_original":  entree.texte,
            "verdict":         resultat["verdict"],
            "explication":     resultat["explication"],
            "score_fiabilite": score_confiance,
            "couleur":         resultat["couleur"],
            "langue":          langue,
            "sources":         sources,
            "sources_fc":      sources_fc,
            "nb_sources":      len(toutes_sources)
        }

    except Exception as e:
        print(f"ERREUR : {e}")
        return {
            "texte_original":  entree.texte,
            "verdict":         "Erreur",
            "explication":     str(e),
            "score_fiabilite": 0.0,
            "couleur":         "orange",
            "langue":          "fr",
            "sources":         [],
            "sources_fc":      [],
            "nb_sources":      0
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)