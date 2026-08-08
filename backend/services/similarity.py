import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.services.data_loader import load_resolved_tickets
from backend.models.schemas import Precedent
from backend.config import TOP_K


class SimilarityEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.resolved_df = None
        self.tfidf_matrix = None
        self._fitted = False

    def fit(self, resolved_df=None):
        if resolved_df is None:
            resolved_df = load_resolved_tickets()
        self.resolved_df = resolved_df.copy()
        self.tfidf_matrix = self.vectorizer.fit_transform(resolved_df['clean_description'])
        self._fitted = True

    def clean(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def get_match_details(self, query_text: str, k: int = TOP_K) -> dict:
        """Vectorize a single ticket with the *fitted* TF-IDF, cosine-match it
        against every resolved ticket, and return the full evidence the dashboard
        animates: query tokens, cosine scores vs the whole DB, and top-k picks."""
        if not self._fitted:
            self.fit()

        query_clean = self.clean(query_text)
        query_vec = self.vectorizer.transform([query_clean])

        features = self.vectorizer.get_feature_names_out()
        sparse = query_vec.tocoo()
        tokens = {}
        for _, j, v in zip(sparse.row, sparse.col, sparse.data):
            tokens[features[j]] = round(float(v), 4)

        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        order = np.argsort(sims)[::-1]

        all_scores = [round(float(x), 4) for x in sims]

        top_k = []
        for idx in order[:k]:
            row = self.resolved_df.iloc[idx]
            top_k.append({
                "ticket_id": row['ticket_id'],
                "description": row['description'],
                "resolution_action": row['resolution_action'],
                "csat": int(row['csat']),
                "similarity": round(float(sims[idx]), 4),
            })

        return {
            "query_text": query_text,
            "query_clean": query_clean,
            "tokens": tokens,
            "num_tokens": len(tokens),
            "vector_dim": self.tfidf_matrix.shape[1],
            "pool_size": self.tfidf_matrix.shape[0],
            "all_scores": all_scores,
            "top_k": top_k,
            "top_similarity": float(sims[order[0]]) if order.size else 0.0,
        }

    def get_top_k(self, query_text: str, k: int = TOP_K) -> list[Precedent]:
        details = self.get_match_details(query_text, k=k)
        return [
            Precedent(
                ticket_id=t['ticket_id'],
                description=t['description'],
                resolution_action=t['resolution_action'],
                similarity=t['similarity'],
                csat=t['csat'],
            )
            for t in details["top_k"]
        ]


similarity_engine = SimilarityEngine()