import logging
import re
from sqlalchemy.orm import Session

# Importa as conexões de banco de dados e os modelos
from .database_mongo import raw_data_collection
from .database_pgsql import SessionLocal
from .models import Product

# Configura o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_price(price_str: str) -> float | None:
    """Extrai um valor float de uma string de preço (ex: '£51.77' -> 51.77)."""
    if not price_str:
        return None
    # Usa regex para encontrar números (incluindo decimais) na string
    match = re.search(r'[\d\.]+', price_str)
    if match:
        try:
            return float(match.group(0))
        except (ValueError, TypeError):
            return None
    return None

def process_bronze_to_gold():
    """
    Lê dados brutos do MongoDB (Bronze), limpa-os e os insere no PostgreSQL (Gold).
    Este processo é idempotente: ele não inserirá registros duplicados.
    """
    logging.info("Iniciando processo de refinamento: Bronze -> Gold...")
    
    processed_count = 0
    skipped_count = 0
    
    # Usar um 'with' statement garante que a sessão do banco de dados seja fechada corretamente.
    with SessionLocal() as db:
        # Busca todos os documentos da camada Bronze (MongoDB)
        raw_documents = raw_data_collection.find()

        for doc in raw_documents:
            raw_data = doc.get("raw_data", {})
            url = raw_data.get("url")
            
            if not url:
                logging.warning(f"Pulando documento {doc['_id']} por falta de URL.")
                continue
                
            # Verifica se um produto com esta URL já existe na camada Gold para evitar duplicatas.
            # Esta é a lógica de idempotência.
            exists = db.query(Product).filter(Product.url == url).first()
            if exists:
                skipped_count += 1
                continue
                
            # Extrai e limpa os dados
            title = raw_data.get("title")
            price_raw = raw_data.get("price")
            price_clean = clean_price(price_raw)
            
            if not all([title, price_clean, url]):
                logging.warning(f"Pulando URL {url} por dados incompletos após limpeza.")
                continue
                
            new_product = Product(title=title, price=price_clean, url=url)
            
            try:
                db.add(new_product)
                db.commit()
                processed_count += 1
                logging.info(f"Produto refinado e salvo: {title}")
            except Exception as e: # Captura exceções genéricas para não parar o loop inteiro
                db.rollback()
                logging.error(f"Falha ao salvar produto da URL {url}: {e}")
            
    logging.info(f"Processo de refinamento concluído. Novos produtos: {processed_count}, Pulados (já existentes): {skipped_count}.")

if __name__ == "__main__":
    process_bronze_to_gold()