import numpy as np
from sentence_transformers import SentenceTransformer
from src.retriever import BM25Retriever
from src.errors import RagLoadError


class HybridRetriever:
    def __init__(self, index_path="data/processed/index.json", embeddings_path="data/embeddings.npy"):
        # 1. On instancie ton Retriever classique
        self.bm25_retriever = BM25Retriever(index_path)

        # CORRECTION : On récupère les chunks directement depuis le BM25 (zéro accès disque supplémentaire !)
        # (Adapte le nom de la variable si ton BM25 utilise un autre nom pour sa liste de chunks)
        self.chunks_data = self.bm25_retriever.all_chunks_data

        # 2. On gère l'Edge Case du fichier manquant
        try:
            self.embeddings_matrix = np.load(embeddings_path)
        except FileNotFoundError:
            raise RagLoadError(
                f"Vector index not found at {embeddings_path}. "
                "Did you run 'index --with-embeddings'?"
            )

        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def search_semantic(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Calcule la similarité cosinus avec numpy"""
        # 1. On vectorise la question
        query_vector = self.embedder.encode([query], show_progress_bar=False)[0]

        # 2. Mathématiques ultra-rapides (Similarité Cosinus)
        dot_products = np.dot(self.embeddings_matrix, query_vector)
        norms_matrix = np.linalg.norm(self.embeddings_matrix, axis=1)
        norm_query = np.linalg.norm(query_vector)

        # Protection contre la division par zéro
        norms_matrix = np.where(norms_matrix == 0, 1e-10, norms_matrix)
        norm_query = 1e-10 if norm_query == 0 else norm_query

        similarities = dot_products / (norms_matrix * norm_query)

        # 3. Tri des meilleurs scores (argsort trie par ordre croissant, [::-1] inverse l'ordre)
        best_indices = np.argsort(similarities)[::-1][:top_k]

        return [(idx, similarities[idx]) for idx in best_indices]

    def search(self, query: str, top_k: int) -> list[dict]:
        pool_size = max(top_k * 2, 60)

        # On demande au BM25 ses scores bruts
        bm25_results = self.bm25_retriever.get_raw_scores(query, pool_size)

        # On demande au réseau de neurones ses scores sémantiques
        semantic_results = self.search_semantic(query, pool_size)
        
        # Algorithme RRF (Reciprocal Rank Fusion)
        rrf_scores = {}
        RRF_K = 60

        for rank, (chunk_idx, _) in enumerate(bm25_results):
            if chunk_idx not in rrf_scores:
                rrf_scores[chunk_idx] = 0.0
            rrf_scores[chunk_idx] += 1.0 / (RRF_K + rank + 1)

        for rank, (chunk_idx, _) in enumerate(semantic_results):
            if chunk_idx not in rrf_scores:
                rrf_scores[chunk_idx] = 0.0
            rrf_scores[chunk_idx] += 1.0 / (RRF_K + rank + 1)

        # Tri et extraction
        sorted_rrf = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        final_top_k_indices = [chunk_idx for chunk_idx, rrf_score in sorted_rrf[:top_k]]

        return [self.chunks_data[idx] for idx in final_top_k_indices]
