import os
import streamlit as st
import requests
import pandas as pd

API_URL = "https://factchecker-production-310f.up.railway.app"

st.set_page_config(
    page_title="FactChecker Bluesky",
    page_icon="🔍",
    layout="wide"
)

# ─── CSS personnalisé ───
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stTextArea textarea { border-radius: 10px; }
    .stButton button {
        background: linear-gradient(90deg, #6C63FF, #48CAE4);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .verdict-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .user-badge {
        background: linear-gradient(90deg, #6C63FF, #48CAE4);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔍 FactChecker Bluesky")
    st.caption("Vérifie si une information est vraie ou fausse grâce à l'IA")

# ─── Connexion utilisateur ───
with st.sidebar:
    st.header("👤 Mon compte")

    if "connecte" not in st.session_state:
        st.session_state.connecte = False
        st.session_state.pseudo = ""

    if not st.session_state.connecte:
        onglet = st.radio("", ["🔑 Connexion", "📝 Inscription"])
        pseudo = st.text_input("Pseudo")
        mdp    = st.text_input("Mot de passe", type="password")

        if onglet == "📝 Inscription":
            if st.button("Créer mon compte"):
                if pseudo and mdp:
                    try:
                        rep = requests.post(
                            f"{API_URL}/inscription",
                            json={"pseudo": pseudo, "mot_de_passe": mdp},
                            timeout=30
                        ).json()
                        if rep.get("succes"):
                            st.success(rep.get("message", "Compte créé !"))
                        else:
                            st.error(rep.get("message", "Erreur inconnue"))
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Remplis tous les champs")

        else:
            if st.button("Se connecter"):
                if pseudo and mdp:
                    try:
                        rep = requests.post(
                            f"{API_URL}/connexion",
                            json={"pseudo": pseudo, "mot_de_passe": mdp},
                            timeout=30
                        ).json()
                        if rep.get("succes"):
                            st.session_state.connecte = True
                            st.session_state.pseudo = pseudo
                            st.rerun()
                        else:
                            st.error(rep.get("message", "Erreur inconnue"))
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Remplis tous les champs")

    else:
        st.markdown(f'<span class="user-badge">✅ {st.session_state.pseudo}</span>', unsafe_allow_html=True)
        st.success("Connecté !")
        if st.button("🚪 Se déconnecter"):
            st.session_state.connecte = False
            st.session_state.pseudo = ""
            st.rerun()

    st.divider()
    st.markdown("**🔗 Liens utiles**")
    st.markdown("- [API Docs](https://factchecker-production-310f.up.railway.app/docs)")
    st.markdown("- [GitHub](https://github.com/abdoulaziz03/factchecker)")

pseudo = st.session_state.get("pseudo", "")

# ─── Vérification ───
st.header("🔎 Vérifier une information")

texte = st.text_area(
    "Colle ici le texte à analyser",
    placeholder="Ex: Les vaccins contiennent des micropuces 5G...",
    height=120
)

if st.button("🔍 Analyser", type="primary"):
    if texte.strip():
        with st.spinner("🤖 Analyse en cours..."):
            try:
                reponse = requests.post(
                    f"{API_URL}/verifier",
                    json={"texte": texte, "utilisateur": pseudo if pseudo else "anonyme"},
                    timeout=60
                )
                resultat = reponse.json()

                couleur_map = {"vert": "success", "orange": "warning", "rouge": "error"}
                niveau = couleur_map.get(resultat["couleur"], "info")
                getattr(st, niveau)(f"**Verdict : {resultat['verdict']}**")

                col1, col2, col3 = st.columns(3)
                with col1:
                    score = resultat["score_fiabilite"] * 100
                    st.metric("Score de fiabilité", f"{score:.0f}%")
                with col2:
                    emoji = "✅" if resultat["couleur"] == "vert" else "⚠️" if resultat["couleur"] == "orange" else "🔴"
                    st.metric("Statut", f"{emoji} {resultat['verdict']}")
                with col3:
                    st.metric("Sources analysées", resultat.get("nb_sources", 0))

                st.info(f"💬 {resultat['explication']}")

                # Langue détectée
                langue = resultat.get("langue", "fr")
                flag = "🇫🇷" if langue == "fr" else "🇬🇧" if langue == "en" else "🌍"
                st.caption(f"{flag} Langue détectée : **{langue}** | 📊 {resultat.get('nb_sources', 0)} sources analysées")

                # Sources fact-checkers
                sources_fc = resultat.get("sources_fc", [])
                if sources_fc:
                    st.subheader("✅ Sources Fact-Checkers officiels")
                    for s in sources_fc:
                        st.markdown(f"🔎 **{s['titre']}**")
                        st.caption(s['extrait'][:150])
                        st.markdown(f"[Voir sur {s['url'][:40]}...]({s['url']})")
                        st.divider()

                # Sources Wikipedia
                sources_wiki = resultat.get("sources_wiki", [])
                if sources_wiki:
                    st.subheader("📖 Sources Wikipedia")
                    for s in sources_wiki:
                        st.markdown(f"📖 **{s['titre']}**")
                        st.caption(s['extrait'][:150])
                        st.markdown(f"[Voir sur Wikipedia]({s['url']})")
                        st.divider()

                # Sources générales
                sources = resultat.get("sources", [])
                if sources:
                    st.subheader("🔗 Sources web")
                    cols = st.columns(min(len(sources), 3))
                    for i, s in enumerate(sources[:3]):
                        with cols[i]:
                            st.markdown(f"**{s['titre'][:50]}...**")
                            st.caption(s['extrait'][:100])
                            st.markdown(f"[Lire →]({s['url']})")

                # Message pour inciter à s'inscrire
                if not pseudo:
                    st.divider()
                    st.info("💡 **Crée un compte** pour sauvegarder ton historique et suivre tes analyses !")

            except Exception as e:
                st.error(f"Erreur : {e}")
    else:
        st.warning("Merci d'entrer un texte à analyser.")

# ─── Historique ───
st.divider()

if pseudo:
    tab1, tab2 = st.tabs([f"📜 Mon historique ({pseudo})", "🌍 Historique global"])

    with tab1:
        try:
            historique = requests.get(
                f"{API_URL}/historique?utilisateur={pseudo}",
                timeout=60
            ).json()

            if historique:
                col1, col2, col3 = st.columns(3)
                total   = len(historique)
                fiables = sum(1 for h in historique if h["verdict"] == "Fiable")
                faux    = sum(1 for h in historique if h["verdict"] == "Probablement faux")

                col1.metric("Total analysé", total)
                col2.metric("✅ Fiables", fiables)
                col3.metric("🔴 Probablement faux", faux)

                verdicts = pd.DataFrame(historique)["verdict"].value_counts()
                st.bar_chart(verdicts)

                df = pd.DataFrame(historique)
                df = df[["date", "texte", "verdict", "score", "explication"]]
                df.columns = ["Date", "Texte", "Verdict", "Score", "Explication"]
                df["Score"] = df["Score"].apply(lambda x: f"{x*100:.0f}%")
                df["Date"]  = df["Date"].apply(lambda x: x[:16].replace("T", " "))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune vérification pour l'instant !")
        except Exception as e:
            st.warning(f"Impossible de charger l'historique : {e}")

    with tab2:
        try:
            historique = requests.get(f"{API_URL}/historique", timeout=60).json()
            if historique:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total global", len(historique))
                col2.metric("✅ Fiables", sum(1 for h in historique if h["verdict"] == "Fiable"))
                col3.metric("🔴 Faux", sum(1 for h in historique if h["verdict"] == "Probablement faux"))

                df = pd.DataFrame(historique)
                df = df[["date", "texte", "verdict", "score", "explication"]]
                df.columns = ["Date", "Texte", "Verdict", "Score", "Explication"]
                df["Score"] = df["Score"].apply(lambda x: f"{x*100:.0f}%")
                df["Date"]  = df["Date"].apply(lambda x: x[:16].replace("T", " "))
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Erreur : {e}")
else:
    st.header("📜 Historique")
    st.warning("🔒 **Connecte-toi** pour accéder à ton historique personnel et suivre toutes tes analyses !")
    col1, col2 = st.columns(2)
    with col1:
        st.info("✅ Sauvegarde automatique de chaque analyse")
    with col2:
        st.info("📊 Graphiques et statistiques personnalisées")