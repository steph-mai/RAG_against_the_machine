import json
import math
from pathlib import Path
from src.tokenizer import Tokenizer
from src.errors import RagLoadError


class BM25Retriever:
    def __init__(self, index_path: str = "data/processed/index.json"):
        self.tokenizer = Tokenizer()
        path = Path(index_path)

        if not path.exists():
            raise RagLoadError(
                f"Index file not found at {index_path}."
                f"Please run the indexer first to generate it.")
        try:
            with open(index_path, mode="r", encoding="utf-8") as f:
                self.index = json.load(f)
        except json.JSONDecodeError as e:
            raise RagLoadError(f"Error decoding JSON from index file: {e}")

        # On extrait les variables de l'index une seule fois ici
        # Cela évite de relire le dictionnaire à chaque recherche !
        self.chunks_number = self.index["chunks_number"]
        self.avg_len = self.index["avg_len_chunks"]
        self.doc_frequency_dict = self.index["document_frequency"]
        self.all_chunks_data = self.index["all_chunks_data"]

    def _clean_query(self, query: str) -> list[str]:
        return self.tokenizer.tokenize(query)

    def get_raw_scores(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """
        Calcule les scores BM25 et renvoie une liste de tuples (index_du_chunk, score).
        """
        clean_query_tokens = self._clean_query(query)

        if not clean_query_tokens:
            return []

        k1 = 1.2
        b = 0.4

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
                    (self.chunks_number - chunk_count_containing_token + 0.5) / (
                        chunk_count_containing_token + 0.5) + 1.0
                        )
                if idf < 0:
                    idf = 0.0

                numerator = term_frequency_in_chunk * (k1 + 1)
                denominator = term_frequency_in_chunk + k1 * (1 - b + b * (
                    tokens_number / self.avg_len))

                score += idf * (numerator / denominator)

            # On ne garde que les chunks pertinents (score > 0)
            if score > 0:
                scores.append((idx, score))

        # On trie par score décroissant
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def search(self, query: str, top_k: int) -> list[dict]:
        """
        L'ancienne méthode, refactorisée pour ne pas dupliquer de code.
        Elle continue de renvoyer la liste de dictionnaires pour la CLI.
        """
        raw_results = self.get_raw_scores(query, top_k)

        final_results = []
        for idx, score in raw_results:
            # On récupère le chunk original en lecture seule, on le copie,
            # et on injecte le score pour garder le comportement initial intact.
            result_chunk = self.all_chunks_data[idx].copy()
            result_chunk["bm25_score"] = score
            final_results.append(result_chunk)

        return final_results
