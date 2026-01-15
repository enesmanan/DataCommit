import os
from dotenv import load_dotenv
from haystack import Pipeline, component
from haystack.components.builders import PromptBuilder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from google import genai
from google.genai import types

load_dotenv()

# Configuration
CHROMA_PERSIST_PATH = "chroma_db"
CHROMA_COLLECTION_NAME = "datacommit_all"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-3-flash-preview"

TEMPLATE = '''
Sen DataCommit podcast serisinin içeriklerinden sorulara cevap veren bir asistansın.

DataCommit, veri bilimi alanında deneyimli uzmanların kariyer yolculuklarını ve teknik bilgilerini paylaştığı bir platformdur.

Aşağıdaki bölümlerden gelen bilgilere dayanarak soruyu cevapla.

Context:
{% for doc in documents %}
---
[Bölüm {{ doc.meta.episode }} - Konuk: {{ doc.meta.guest }}]
{{ doc.content }}
---
{% endfor %}

Soru: {{question}}

Cevabını verirken:
1. İlgili bilgileri sentezle
2. Her önemli bilgi için kaynak göster: (Bölüm X, Konuk adı)
3. Birden fazla bölümden bilgi varsa hepsini belirt

Cevap:
'''


@component
class GeminiGenerator:
    def __init__(self, model: str = "gemini-3-flash-preview", temperature: float = 0.5):
        self.model = model
        self.temperature = temperature
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    @component.output_types(replies=list)
    def run(self, parts: str):
        response = self.client.models.generate_content(
            model=self.model,
            contents=parts,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        return {"replies": [response.text]}


# Lazy loading - initialize on first use
_pipeline = None
_document_store = None
_query_embedder = None
_retriever = None
_prompt_builder = None
_generator = None


def get_document_store():
    global _document_store
    if _document_store is None:
        _document_store = ChromaDocumentStore(
            persist_path=CHROMA_PERSIST_PATH,
            collection_name=CHROMA_COLLECTION_NAME
        )
    return _document_store


def get_pipeline():
    global _pipeline, _query_embedder, _retriever, _prompt_builder, _generator
    
    if _pipeline is None:
        print("Initializing RAG pipeline...")
        
        _query_embedder = SentenceTransformersTextEmbedder(model=EMBEDDING_MODEL)
        _query_embedder.warm_up()
        
        _retriever = ChromaEmbeddingRetriever(document_store=get_document_store(), top_k=5)
        _prompt_builder = PromptBuilder(template=TEMPLATE, required_variables=["documents", "question"])
        _generator = GeminiGenerator(model=GEMINI_MODEL, temperature=0.5)
        
        _pipeline = Pipeline()
        _pipeline.add_component("query_embedder", _query_embedder)
        _pipeline.add_component("retriever", _retriever)
        _pipeline.add_component("prompt_builder", _prompt_builder)
        _pipeline.add_component("llm", _generator)
        
        _pipeline.connect("query_embedder.embedding", "retriever.query_embedding")
        _pipeline.connect("retriever.documents", "prompt_builder.documents")
        _pipeline.connect("prompt_builder.prompt", "llm.parts")
        
        print("RAG pipeline ready!")
    
    return _pipeline


def respond_with_sources(query: str, top_k: int = 5):
    if not query.strip():
        return "", []
    
    get_pipeline()
    
    embedding = _query_embedder.run(text=query)["embedding"]
    docs = _retriever.run(query_embedding=embedding, top_k=top_k)["documents"]
    
    prompt = _prompt_builder.run(documents=docs, question=query)["prompt"]
    response = _generator.run(parts=prompt)["replies"][0]
    
    sources = []
    seen = set()
    for doc in docs:
        key = (doc.meta.get("episode"), doc.meta.get("guest"))
        if key not in seen:
            sources.append({
                "episode": doc.meta.get("episode"),
                "guest": doc.meta.get("guest"),
                "score": doc.score
            })
            seen.add(key)
    
    return response, sources


def show_retrieved_chunks(query: str, top_k: int = 5):
    get_pipeline()
    
    embedding = _query_embedder.run(text=query)["embedding"]
    docs = _retriever.run(query_embedding=embedding, top_k=top_k)["documents"]
    
    print(f"Query: {query}\n")
    print(f"Retrieved {len(docs)} chunks:\n" + "=" * 80)
    
    for i, doc in enumerate(docs, 1):
        ep = doc.meta.get("episode", "?")
        guest = doc.meta.get("guest", "Unknown")
        print(f"\n[Chunk {i}] Bölüm {ep} - {guest} | Score: {doc.score:.4f}")
        print("-" * 40)
        print(doc.content[:400] + "..." if len(doc.content) > 400 else doc.content)
        print("=" * 80)
    
    return docs


def query_datacommit(query: str, show_chunks: bool = False):
    print("\n" + "=" * 80)
    print(f"SORU: {query}")
    print("=" * 80)
    
    if show_chunks:
        print("\n--- Retrieved Chunks ---")
        show_retrieved_chunks(query)
    
    response, sources = respond_with_sources(query)
    
    print("\n--- CEVAP ---")
    print(response)
    
    print("\n--- KAYNAKLAR ---")
    for src in sources:
        print(f"  • Bölüm {src['episode']}: {src['guest']} (relevance: {src['score']:.4f})")
    
    return response, sources


class _DocumentStoreProxy:
    def count_documents(self):
        return get_document_store().count_documents()

document_store = _DocumentStoreProxy()


if __name__ == "__main__":
    doc_count = document_store.count_documents()
    if doc_count == 0:
        print("No documents found! Run 'python create_database.py' first.")
    else:
        print(f"Loaded {doc_count} chunks from all episodes\n")
        query_datacommit("Jr lar nasıl iş bulur?", show_chunks=False)
