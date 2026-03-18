# --- MongoDB ---
import os
from dotenv import load_dotenv
load_dotenv()


MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://carinebasset490_db_user:mmBcmdnFtTf8dbrL@cluster0.aidiodt.mongodb.net/")
COLLECTION_RAW   = "posts_bruts"
COLLECTION_CLEAN = "posts_propres"

# --- Bluesky API ---
BLUESKY_USERNAME = "azizshamark.bsky.social"
BLUESKY_PASSWORD = "bpvd-bwfs-3g6k-pj7i"

# --- Mots-clés à surveiller ---
KEYWORDS = [
    "fake news",
    "rumeur",
    "intox",
    "vérification",
    "fact check",
]

# --- Machine Learning ---
NB_CLUSTERS = 3
MAX_FEATURES = 5000

# --- API ---
API_HOST = "0.0.0.0"
API_PORT = 8000