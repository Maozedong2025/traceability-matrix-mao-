from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def retrieve_similar(source_text, candidates, top_k=3):
    if not candidates:
        return []
    corpus = [source_text] + [c.get("item_text","") for c in candidates]
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        mat = vec.fit_transform(corpus)
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
    except Exception:
        return []
    ranked = sorted(zip(candidates, sims), key=lambda x: x[1], reverse=True)
    return [{**cand, "rag_score": float(score), "rag_reason": f"Retrieved by local RAG similarity. Score: {score:.2f}"} for cand, score in ranked[:top_k]]
