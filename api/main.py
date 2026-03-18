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

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client_groq = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="FactChecker API", version="4.0.0")


class TexteEntrant(BaseModel):
    texte: str
    utilisateur: str = "anonyme"


class Utilisateur(BaseModel):
    pseudo: str
    mot_de_passe: str


@app.get("/")
def accueil():
    return {"message": "FactChecker API en ligne ✅"}


@app.post("/inscription")
def inscription(user: Utilisateur):
    try:
        from pymongo import MongoClient
        MONGO_URL = os.environ.get("MONGO_URL", "")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000, tlsInsecure=True)
        db = client["factchecker"]

        if db["utilisateurs"].find_one({"pseudo": user.pseudo}):
            client.close()
            return {"succes": False, "message": "Ce pseudo est déjà pris"}

        mot_de_passe_hash = bcrypt.hashpw(
            user.mot_de_passe.encode("utf-8"),
            bcrypt.gensalt()
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
        from pymongo import MongoClient
        MONGO_URL = os.environ.get("MONGO_URL", "")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000, tlsInsecure=True)
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
        else:
            return {"succes": False, "message": "Mot de passe incorrect"}

    except Exception as e:
        return {"succes": False, "message": str(e)}


@app.get("/historique")
def get_historique(utilisateur: str = None):
    try:
        from pymongo import MongoClient
        MONGO_URL = os.environ.get("MONGO_URL", "")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000, tlsInsecure=True)
        db = client["factchecker"]
        filtre = {"utilisateur": utilisateur} if utilisateur else {}
        historique = list(db["historique"].find(filtre, {"_id": 0}).sort("date", -1).limit(50))
        client.close()
        return historique
    except Exception as e:
        print(f"MongoDB : {e}")
        return []


def rechercher_sources(texte, nb=3):
    try:
        with DDGS() as ddgs:
            resultats = list(ddgs.text(texte, max_results=nb))
        sources = []
        for r in resultats:
            sources.append({
                "titre":   r.get("title", ""),
                "url":     r.get("href", ""),
                "extrait": r.get("body", "")[:200]
            })
        return sources
    except Exception as e:
        print(f"Erreur recherche web : {e}")
        return []


@app.post("/verifier")
def verifier_information(entree: TexteEntrant):
    try:
        sources = rechercher_sources(entree.texte)
        contexte_sources = "\n".join(
            [f"- {s['titre']} : {s['extrait']}" for s in sources]
        ) if sources else "Aucune source trouvée."

        prompt = f"""Tu es un expert en fact-checking. Analyse cette affirmation en tenant compte des sources trouvées sur le web.
Réponds UNIQUEMENT en JSON valide, sans texte avant ou après.

Affirmation : "{entree.texte}"

Sources trouvées sur le web :
{contexte_sources}

Réponds avec ce format JSON exact :
{{
  "verdict": "Fiable" ou "À vérifier" ou "Probablement faux",
  "score": 0.8,
  "couleur": "vert" ou "orange" ou "rouge",
  "explication": "Une phrase courte expliquant pourquoi en tenant compte des sources"
}}"""

        reponse = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )

        contenu = reponse.choices[0].message.content
        match = re.search(r'\{.*\}', contenu, re.DOTALL)
        resultat = json.loads(match.group())

        try:
            from pymongo import MongoClient
            MONGO_URL = os.environ.get("MONGO_URL", "")
            client_mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000, tlsInsecure=True)
            db = client_mongo["factchecker"]
            db["historique"].insert_one({
                "texte":        entree.texte,
                "utilisateur":  entree.utilisateur,
                "verdict":      resultat["verdict"],
                "explication":  resultat["explication"],
                "score":        float(resultat["score"]),
                "couleur":      resultat["couleur"],
                "sources":      sources,
                "date":         datetime.now().isoformat()
            })
            client_mongo.close()
        except Exception as mongo_err:
            print(f"MongoDB : {mongo_err}")

        return {
            "texte_original":  entree.texte,
            "verdict":         resultat["verdict"],
            "explication":     resultat["explication"],
            "score_fiabilite": float(resultat["score"]),
            "couleur":         resultat["couleur"],
            "sources":         sources
        }

    except Exception as e:
        print(f"ERREUR : {e}")
        return {
            "texte_original":  entree.texte,
            "verdict":         "Erreur",
            "explication":     str(e),
            "score_fiabilite": 0.0,
            "couleur":         "orange",
            "sources":         []
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)