import json
import math
from pathlib import Path
from src.tokenizer import Tokenizer
from src.errors import RagLoadError


class BM25Retriever:
    """Retrieve relevant text chunks using the BM25 ranking function.

    Args:
        index_path: Path to the processed index JSON file.
    """

    def __init__(self, index_path: str = "data/processed/index.json"):
        """Initialize the BM25 retriever with a processed index.

        Args:
            index_path: Path to the processed index JSON file.

        Raises:
            RagLoadError: If the index file does not exist or cannot be parsed.
        """
        self.tokenizer = Tokenizer()
        index_path_obj = Path(index_path)

        if not index_path_obj.exists():
            raise RagLoadError(
                f"Index file not found at {index_path}."
                f"Please run the indexer first to generate it.")
        try:
            with open(index_path, mode="r", encoding="utf-8") as f:
                self.index = json.load(f)
        except json.JSONDecodeError as e:
            raise RagLoadError(f"Error decoding JSON from index file: {e}")

        self.chunks_number = self.index["chunks_number"]
        self.avg_len = self.index["avg_len_chunks"]
        self.doc_frequency_dict = self.index["document_frequency"]
        self.all_chunks_data = self.index["all_chunks_data"]

    def _clean_query(self, query: str) -> list[str]:
        """Tokenize and clean a query string.

        Args:
            query: Raw user query.

        Returns:
            List of cleaned tokens.
        """
        return self.tokenizer.tokenize(query)

    def get_raw_scores(
            self, query: str, top_k: int
            ) -> list[tuple[int, float]]:
        """Compute BM25 scores for the query and return the top-ranked chunks.

        Args:
            query: Query string to rank.
            top_k: Maximum number of chunk results to return.

        Returns:
            List of tuples whose first element is the chunk index and second is
            the BM25 score.
        """
        clean_query_tokens = self._clean_query(query)

        if not clean_query_tokens:
            return []

        k1 = 1.2
        b = 0.4
        d = 0.5

        scores = []

        for idx, chunk_data in enumerate(self.all_chunks_data):
            score = 0.0
            term_frequency_dict = chunk_data["term_frequency"]
            tokens_number = chunk_data["clean_tokens_number"]

            for query_token in clean_query_tokens:
                if query_token not in term_frequency_dict:
                    continue

                term_frequency_in_chunk = term_frequency_dict[query_token]
                chunk_count_containing_token = self.doc_frequency_dict.get(
                    query_token, 0)

                idf = math.log(
                    (
                        self.chunks_number - chunk_count_containing_token + d
                        ) / (
                        chunk_count_containing_token + d) + 1.0
                        )
                if idf < 0:
                    idf = 0.0

                numerator = term_frequency_in_chunk * (k1 + 1)
                denominator = term_frequency_in_chunk + k1 * (1 - b + b * (
                    tokens_number / self.avg_len))

                score += idf * (numerator / denominator)

            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def search(self, query: str, top_k: int) -> list[dict]:
        """Search for relevant chunks and return enriched results.

        Args:
            query: Query string to search.
            top_k: Maximum number of chunk results to return.

        Returns:
            List of dictionaries containing the chunk data enriched with a
            BM25 score.
        """
        raw_results = self.get_raw_scores(query, top_k)

        final_results = []
        for idx, score in raw_results:
            result_chunk = self.all_chunks_data[idx].copy()
            result_chunk["bm25_score"] = score
            final_results.append(result_chunk)

        return final_results
