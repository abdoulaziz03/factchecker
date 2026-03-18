FROM apache/airflow:2.8.1
USER airflow
RUN pip install --no-cache-dir atproto pymongo scikit-learn pandas joblib duckduckgo-search==3.9.3 groq