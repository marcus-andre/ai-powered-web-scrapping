import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Pega a URL do MongoDB (fornecida pelo docker-compose)
# O fallback padrão ajuda em testes locais fora do Docker
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/raw_data_db")

# Inicializa o cliente do MongoDB
client = MongoClient(MONGO_URL)

# Define o banco de dados e a coleção (tabela) da nossa camada Bronze
db = client.get_database() # Pega o banco da URL (raw_data_db)
raw_data_collection = db["raw_html_payloads"]