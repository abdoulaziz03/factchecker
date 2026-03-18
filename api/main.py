import os
import sys
import json
import re
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from pymongo import MongoClient
from ddgs import DDGS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "config"))

from settings import MONGO_URL, MONGO_DB

from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client_groq = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="FactChecker API", version="4.0.0")


class TexteEntrant(BaseModel):
    texte: str


@app.get("/")
def accueil():
    return {"message": "FactChecker API en ligne ✅"}


@app.get("/historique")
def get_historique():
    client = MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    historique = list(
        db["historique"]
        .find({}, {"_id": 0})
        .sort("date", -1)
        .limit(50)
    )
    client.close()
    return historique


def rechercher_sources(texte, nb=3):
    """Recherche des articles liés à l'affirmation via DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            resultats = list(ddgs.text(texte, max_results=nb))
        sources = []
        for r in resultats:
            sources.append({
                "titre": r.get("title", ""),
                "url":   r.get("href", ""),
                "extrait": r.get("body", "")[:200]
            })
        return sources
    except Exception as e:
        print(f"Erreur recherche web : {e}")
        return []


@app.post("/verifier")
def verifier_information(entree: TexteEntrant):
    try:
        # Recherche de sources en parallèle
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

        # Sauvegarde dans MongoDB
        client_mongo = MongoClient(MONGO_URL)
        db = client_mongo[MONGO_DB]
        db["historique"].insert_one({
            "texte":       entree.texte,
            "verdict":     resultat["verdict"],
            "explication": resultat["explication"],
            "score":       float(resultat["score"]),
            "couleur":     resultat["couleur"],
            "sources":     sources,
            "date":        datetime.now().isoformat()
        })
        client_mongo.close()

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