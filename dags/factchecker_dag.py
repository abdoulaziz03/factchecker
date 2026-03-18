from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

sys.path.insert(0, "/opt/airflow/collecte")
sys.path.insert(0, "/opt/airflow/nlp")
sys.path.insert(0, "/opt/airflow/ml")
sys.path.insert(0, "/opt/airflow/config")

default_args = {
    "owner": "factchecker",
    "start_date": datetime(2026, 1, 1),
}

dag = DAG(
    "factchecker_pipeline",
    default_args=default_args,
    schedule_interval="@hourly",
    catchup=False
)

def tache_collecte():
    from bluesky_scraper import lancer_collecte
    lancer_collecte()

def tache_nettoyage():
    from nettoyage import traiter_tous_les_posts
    traiter_tous_les_posts()

def tache_ml():
    from model import entrainer_modele
    entrainer_modele()

t1 = PythonOperator(task_id="collecte_bluesky",  python_callable=tache_collecte, dag=dag)
t2 = PythonOperator(task_id="nettoyage_nlp",     python_callable=tache_nettoyage, dag=dag)
t3 = PythonOperator(task_id="entrainement_ml",   python_callable=tache_ml, dag=dag)

t1 >> t2 >> t3