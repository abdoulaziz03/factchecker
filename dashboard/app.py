import sys
import os
import streamlit as st
import requests
import pandas as pd

# URL de l'API Railway
API_URL = "https://factchecker-production-310f.up.railway.app"

st.set_page_config(
    page_title="FactChecker Bluesky",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 FactChecker Bluesky")
st.caption("Vérifie si une information est vraie ou fausse")

# ─── Test connexion API ───
try:
    test = requests.get(f"{API_URL}/", timeout=5)
    st.success("✅ API connectée")
except:
    st.error("❌ API non accessible")
    st.stop()

# ─── Vérification ───
st.header("🔎 Vérifier une information")

texte = st.text_area(
    "Colle ici le texte à analyser",
    placeholder="Ex: Les vaccins contiennent des micropuces 5G...",
    height=120
)

if st.button("Analyser", type="primary"):
    if texte.strip():
        with st.spinner("Analyse en cours..."):
            reponse = requests.post(
                f"{API_URL}/verifier",
                json={"texte": texte},
                timeout=30
            )
            resultat = reponse.json()

            couleur_map = {"vert": "success", "orange": "warning", "rouge": "error"}
            niveau = couleur_map.get(resultat["couleur"], "info")
            getattr(st, niveau)(f"**Verdict : {resultat['verdict']}**")
            st.metric("Score de fiabilité", f"{resultat['score_fiabilite']*100:.0f}%")
            st.info(f"💬 {resultat['explication']}")

            # Affichage des sources
            sources = resultat.get("sources", [])
            if sources:
                st.subheader("🔗 Sources trouvées sur le web")
                for s in sources:
                    st.markdown(f"**{s['titre']}**")
                    st.caption(s['extrait'])
                    st.markdown(f"[Lire l'article]({s['url']})")
                    st.divider()
    else:
        st.warning("Merci d'entrer un texte à analyser.")

# ─── Historique ───
st.divider()
st.header("📜 Historique des vérifications")

try:
    historique = requests.get(f"{API_URL}/historique", timeout=5).json()

    if historique:
        col1, col2, col3 = st.columns(3)
        total  = len(historique)
        fiables = sum(1 for h in historique if h["verdict"] == "Fiable")
        faux    = sum(1 for h in historique if h["verdict"] == "Probablement faux")

        col1.metric("Total analysé", total)
        col2.metric("✅ Fiables", fiables)
        col3.metric("🔴 Probablement faux", faux)

        df = pd.DataFrame(historique)
        df = df[["date", "texte", "verdict", "score", "explication"]]
        df.columns = ["Date", "Texte", "Verdict", "Score", "Explication"]
        df["Score"] = df["Score"].apply(lambda x: f"{x*100:.0f}%")
        df["Date"]  = df["Date"].apply(lambda x: x[:16].replace("T", " "))
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune vérification pour l'instant — analyse un texte ci-dessus !")

except Exception as e:
    st.warning(f"Impossible de charger l'historique : {e}")