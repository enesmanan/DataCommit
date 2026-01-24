import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from rag_pipeline import respond_with_sources, document_store

app = Flask(__name__)
CORS(app)

GUEST_IMAGES = {
    1: {"name": "Kaan Bıçakçı", "image": "kaan_bicakci.jpg"},
    2: {"name": "Bilge Yücel", "image": "bilge_yucel.jpg"},
    3: {"name": "Alara Dirik", "image": "alara_dirik.jpg"},
    4: {"name": "Olgun Aydın", "image": "olgun_aydin.jpg"},
    5: {"name": "Eren Akbaba", "image": "eren_akbaba.jpg"},
    6: {"name": "Taner Sekmen", "image": "taner_sekmen.jpg"},
    7: {"name": "Murat Şahin", "image": "murat_sahin.jpg"},
    8: {"name": "Göker Güner", "image": "goker_guner.jpg"},
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    query = data.get("query", "")
    
    if not query.strip():
        return jsonify({"error": "Empty query"}), 400
    
    response, sources = respond_with_sources(query, top_k=5)
    
    sources_with_images = []
    for src in sources:
        ep = src["episode"]
        guest_info = GUEST_IMAGES.get(ep, {"name": src["guest"], "image": "default.jpg"})
        sources_with_images.append({
            "episode": ep,
            "guest": src["guest"],
            "image": guest_info["image"],
            "score": src["score"]
        })
    
    return jsonify({
        "response": response,
        "sources": sources_with_images
    })


@app.route("/api/status")
def status():
    doc_count = document_store.count_documents()
    return jsonify({
        "status": "ok",
        "documents": doc_count,
        "guests": list(GUEST_IMAGES.values())
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Documents loaded: {document_store.count_documents()}")
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
