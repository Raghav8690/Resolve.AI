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
    
    def get_top_k(self, query_text: str, k: int = TOP_K) -> list[Precedent]:
        if not self._fitted:
            self.fit()
        
        query_clean = query_text.lower()
        query_clean = re.sub(r'[^\w\s]', ' ', query_clean)
        query_clean = re.sub(r'\s+', ' ', query_clean).strip()
        
        query_vec = self.vectorizer.transform([query_clean])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        top_indices = np.argsort(similarities)[::-1][:k]
        
        precedents = []
        for idx in top_indices:
            row = self.resolved_df.iloc[idx]
            precedents.append(Precedent(
                ticket_id=row['ticket_id'],
                description=row['description'],
                resolution_action=row['resolution_action'],
                similarity=float(similarities[idx]),
                csat=int(row['csat'])
            ))
        return precedents

similarity_engine = SimilarityEngine()
