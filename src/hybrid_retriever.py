import chromadb
from pathlib import Path
from src.retriever import BM25Retriever
from src.errors import RagLoadError


class HybridRetriever:
    """Combine BM25 lexical retrieval with ChromaDB semantic retrieval.

    Args:
        index_path: Path to the processed index JSON file.
        chroma_persist_dir: Directory where the ChromaDB persistent collection
            is stored.
    """

    def __init__(
            self,
            index_path="data/processed/index.json",
            chroma_persist_dir="data/chroma"
            ):
        """Initialize the hybrid retriever with BM25 and ChromaDB.

        Args:
            index_path: Path to the processed index JSON file.
            chroma_persist_dir: Directory where the ChromaDB persistent
                collection is stored.

        Raises:
            RagLoadError: If the ChromaDB collection cannot be loaded.
        """
        self.bm25_retriever = BM25Retriever(index_path)
        self.chunks_data = self.bm25_retriever.all_chunks_data

        try:
            self.client = chromadb.PersistentClient(path=chroma_persist_dir)
            self.collection = self.client.get_collection(
                name="codebase_chunks")
        except Exception:
            raise RagLoadError(
                f"ChromaDB collection not found at {chroma_persist_dir}. "
                "Did you run the vector indexing step?"
            )

    def search_semantic(
            self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Search semantically using the ChromaDB collection.

        Args:
            query: Query string to embed and search.
            top_k: Maximum number of semantic results to return.

        Returns:
            List of tuples whose first element is the chunk index and second
            is the semantic similarity score.
        """
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
        """Fuse BM25 and semantic retrieval results
        using reciprocal rank fusion (rrf algorithm)

        Args:
            query: Query string to search.
            top_k: Maximum number of final results to return.

        Returns:
            List of dictionaries containing the top-ranked chunks.
        """
        pool_results_size = max(top_k * 2, 60)

        bm25_results = self.bm25_retriever.get_raw_scores(
            query, pool_results_size)
        semantic_results = self.search_semantic(query, pool_results_size)

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
            chunk_idx for chunk_idx, _ in sorted_rrf[:top_k]
        ]

        return [self.chunks_data[idx] for idx in final_top_k_indices]
