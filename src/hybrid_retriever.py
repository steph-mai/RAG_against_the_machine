import chromadb
from src.retriever import BM25Retriever
from src.errors import RagLoadError


class HybridRetriever:
    def __init__(
            self,
            index_path="data/processed/index.json",
            chroma_persist_dir="data/chroma"
            ):
        """Initialize the hybrid retriever with BM25 and ChromaDB."""
        self.bm25_retriever = BM25Retriever(index_path)
        self.chunks_data = self.bm25_retriever.all_chunks_data

        try:
            self.client = chromadb.PersistentClient(path=chroma_persist_dir)
            self.collection = self.client.get_collection(name="codebase_chunks")
        except Exception:
            raise RagLoadError(
                f"ChromaDB collection not found at {chroma_persist_dir}. "
                "Did you run the vector indexing step?"
            )

    def search_semantic(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Semantic search managed natively by ChromaDB."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        ids = results['ids'][0]
        distances = results['distances'][0]

        semantic_results = []
        for chunk_id, distance in zip(ids, distances):
            chunk_idx = int(chunk_id)
            score = 1.0 - distance
            semantic_results.append((chunk_idx, score))

        return semantic_results

    def search(self, query: str, top_k: int) -> list[dict]:
        """Fusionne BM25 et Recherche Sémantique via RRF."""
        pool_size = max(top_k * 2, 60)

        bm25_results = self.bm25_retriever.get_raw_scores(query, pool_size)
        semantic_results = self.search_semantic(query, pool_size)

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

        sorted_rrf = sorted(
            rrf_scores.items(), key=lambda item: item[1], reverse=True
        )
        final_top_k_indices = [
            chunk_idx for chunk_idx, rrf_score in sorted_rrf[:top_k]
        ]

        return [self.chunks_data[idx] for idx in final_top_k_indices]
