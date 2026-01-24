import os
from pathlib import Path
from dotenv import load_dotenv
from haystack.components.converters import TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

load_dotenv()

# Configuration
DATA_DIR = Path("data/Final")
CHROMA_PERSIST_PATH = "chroma_db"
CHROMA_COLLECTION_NAME = "datacommit_all"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

EPISODES = [
    {"file": "datacommit_1_kaan_bicakci_speakers_cleaned_named.txt", "guest": "Kaan Bıçakçı", "episode": 1},
    {"file": "datacommit_2_bilge_yucel_speakers_cleaned_named.txt", "guest": "Bilge Yücel", "episode": 2},
    {"file": "datacommit_3_alara_dirik_speakers_cleaned_named.txt", "guest": "Alara Dirik", "episode": 3},
    {"file": "datacommit_4_olgun_aydin_speakers_cleaned_named.txt", "guest": "Olgun Aydın", "episode": 4},
    {"file": "datacommit_5_eren_akbaba_speakers_cleaned_named.txt", "guest": "Eren Akbaba", "episode": 5},
    {"file": "datacommit_6_taner_sekmen_speakers_cleaned_named.txt", "guest": "Taner Sekmen", "episode": 6},
    {"file": "datacommit_7_murat_sahin_speakers_cleaned_named.txt", "guest": "Murat Şahin", "episode": 7},
    {"file": "datacommit_8_goker_guner_speakers_cleaned_named.txt", "guest": "Göker Güner", "episode": 8},
]


def create_database():
    document_store = ChromaDocumentStore(
        persist_path=CHROMA_PERSIST_PATH,
        collection_name=CHROMA_COLLECTION_NAME
    )
    
    if document_store.count_documents() > 0:
        print(f"Database already has {document_store.count_documents()} chunks")
        print("Delete 'chroma_db' folder to re-ingest")
        return document_store
    
    all_docs = []
    txt_converter = TextFileToDocument()
    text_splitter = DocumentSplitter(
        split_by="word",
        split_length=800,
        split_overlap=200,
        split_threshold=10
    )
    
    for ep in EPISODES:
        file_path = DATA_DIR / ep["file"]
        if not file_path.exists():
            print(f"[!] Skipping Episode {ep['episode']} - file not found: {ep['file']}")
            continue
        
        raw_docs = txt_converter.run(sources=[str(file_path)])["documents"]
        
        for doc in raw_docs:
            doc.meta["episode"] = ep["episode"]
            doc.meta["guest"] = ep["guest"]
        
        split_docs = text_splitter.run(documents=raw_docs)["documents"]
        print(f"[+] Episode {ep['episode']} ({ep['guest']}): {len(split_docs)} chunks")
        all_docs.extend(split_docs)
    
    print(f"\n[*] Embedding {len(all_docs)} chunks...")
    doc_embedder = SentenceTransformersDocumentEmbedder(model=EMBEDDING_MODEL)
    doc_embedder.warm_up()
    embedded_docs = doc_embedder.run(documents=all_docs)["documents"]
    
    print(f"[*] Writing to ChromaDB...")
    document_store.write_documents(embedded_docs)
    print(f"[✓] Ingested {len(embedded_docs)} chunks from {len(EPISODES)} episodes")
    
    return document_store


if __name__ == "__main__":
    create_database()
