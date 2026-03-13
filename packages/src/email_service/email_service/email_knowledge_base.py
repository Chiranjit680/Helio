import psycopg2
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
# Load environment variables
from pathlib import Path    
base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")


# 1. Setup ChromaDB (Persistent Client)
# This creates a folder named 'my_chroma_db' in your current directory
chroma_client = chromadb.PersistentClient(path="./my_chroma_db")

# Use a standard embedding model (HuggingFace)
# This handles the "text to vector" conversion automatically
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create or get a collection
collection = chroma_client.get_or_create_collection(
    name="email_knowledge_base", 
    embedding_function=sentence_transformer_ef
)

# 2. Database Config
database_url= os.getenv("DATABASE_URL", "postgresql://postgres:unlockit@localhost/Helio")

def sync_postgres_to_chroma():
    try:
        conn = psycopg2.connect(
    host="localhost",
    database="Helio",
    user="postgres",
    password="unlockit",
    port="5432"
)
        cur = conn.cursor()
        
        # Fetching ID and the actual text
        cur.execute("SELECT id,from_email, subject, body FROM emails;")
        rows = cur.fetchall()
        
# Assuming SELECT id, content_text, is_read FROM documents_table;
# row[0] = id, row[1] = content, row[2] = is_read

        ids = [str(row[0]) for row in rows ]
        documents = [f"From: {row[1]}\nSubject: {row[2]}\nBody: {row[3]}" for row in rows ]  # The text content to be embedded
        # You can also store the original ID or category as metadata
        metadatas = [{"source": "postgres", "original_id": row[0]} for row in rows]

        # 3. Add to Chroma
        # Chroma handles the vectorization internally using the EF we defined
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"Successfully synced {len(ids)} documents to ChromaDB.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    
    
    # Example Query
    results = collection.query(
        query_texts=["java developer?"],
        n_results=2
    )
    print("Search Results:", results["documents"][0][0])
    print(type(results["documents"][0][0]))