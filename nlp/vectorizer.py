import math
from typing import List, Dict, Tuple, Union

class TfidfVectorizer:
    """
    A custom TF-IDF (Term Frequency-Inverse Document Frequency) implementation.
    """
    def __init__(self, max_features: int = None):
        self.max_features = max_features
        self.vocabulary_: Dict[str, int] = {}
        self.idf_: Dict[str, float] = {}
        self.feature_names_: List[str] = []
        
    def _compute_tf(self, document_tokens: List[str]) -> Dict[str, float]:
        """Compute Term Frequency (TF) for a single document."""
        tf_dict = {}
        doc_length = len(document_tokens)
        
        if doc_length == 0:
            return tf_dict
            
        for token in document_tokens:
            tf_dict[token] = tf_dict.get(token, 0) + 1
            
        for token in tf_dict:
            tf_dict[token] = tf_dict[token] / doc_length
            
        return tf_dict

    def fit(self, documents: List[List[str]]) -> 'TfidfVectorizer':
        """Learn vocabulary and IDF weights from list of preprocessed token lists."""
        total_documents = len(documents)
        document_frequencies = {}
        
        # Calculate Document Frequencies (DF)
        for doc_tokens in documents:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                document_frequencies[token] = document_frequencies.get(token, 0) + 1
                
        # Sort by frequency if max_features is set
        if self.max_features and self.max_features < len(document_frequencies):
            sorted_tokens = sorted(document_frequencies.items(), key=lambda x: x[1], reverse=True)
            top_tokens = [token for token, freq in sorted_tokens[:self.max_features]]
            
            # Filter document_frequencies to only include top tokens
            document_frequencies = {k: v for k, v in document_frequencies.items() if k in top_tokens}
            
        # Compute IDF and build vocabulary
        for idx, (token, df) in enumerate(document_frequencies.items()):
            self.vocabulary_[token] = idx
            self.feature_names_.append(token)
            
            # IDF = log(N / (df + 1)) + 1 to avoid division by zero and negative values
            self.idf_[token] = math.log((total_documents + 1) / (df + 1)) + 1.0
            
        return self
        
    def transform(self, documents: List[List[str]]) -> List[Dict[str, float]]:
        """Convert documents to TF-IDF vectors (dict of term->weight)."""
        if not self.vocabulary_:
            raise ValueError("Vocabulary not fitted. Call fit() first.")
            
        tfidf_vectors = []
        
        for doc_tokens in documents:
            tf_dict = self._compute_tf(doc_tokens)
            doc_tfidf = {}
            
            for token, tf in tf_dict.items():
                if token in self.vocabulary_:
                    doc_tfidf[token] = tf * self.idf_[token]
                    
            # Normalize vector (L2 norm)
            norm = math.sqrt(sum(val ** 2 for val in doc_tfidf.values()))
            if norm > 0:
                for token in doc_tfidf:
                    doc_tfidf[token] = doc_tfidf[token] / norm
                    
            tfidf_vectors.append(doc_tfidf)
            
        return tfidf_vectors
        
    def fit_transform(self, documents: List[List[str]]) -> List[Dict[str, float]]:
        """Fit then transform."""
        return self.fit(documents).transform(documents)
        
    def get_feature_names(self) -> List[str]:
        """Return vocabulary list."""
        return self.feature_names_
        
    @staticmethod
    def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Compute cosine similarity between two TF-IDF vectors (dictionaries)."""
        intersection = set(vec1.keys()) & set(vec2.keys())
        
        dot_product = sum(vec1[token] * vec2[token] for token in intersection)
        
        norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
