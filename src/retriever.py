import json
import math
from pathlib import Path
from src.tokenizer import Tokenizer
from src.errors import RagLoadError


class BM25Retriever():
    def __init__(self, index_path: str = "data/processed/index.json"):
        self.tokenizer = Tokenizer()
        path = Path(index_path)

        if not path.exists():
            raise RagLoadError(
                f"Index file not found at {index_path}."
                f"Please run the indexer first to generate it.")
        try:
            with open(
                    "data/processed/index.json", mode="r", encoding="utf-8"
                    ) as f:
                self.index = json.load(f)
        except json.JSONDecodeError as e:
            raise RagLoadError(f"Error decoding JSON from index file: {e}")

    def _clean_query(self, query: str) -> list[str]:
        return self.tokenizer.normalize_and_clean_raw_text(query)

    def search(self, query: str, k: int
               ) -> list[dict[str, str | int | dict[str, int]]]:
        clean_query_tokens = self._clean_query(query)

        print(f"DEBUG - Tokens de la requête : {clean_query_tokens}")

        if not clean_query_tokens:
            return []

        # k_1 et b : Des constantes de réglage (paramètres de tuning).
        # k_1 (souvent réglé entre 1.2 et 2.0) contrôle la saturation du
        # TF (si un mot apparaît 50 fois au lieu de 5 fois, son score n'est
        # pas multiplié par 10, il s'arrête de croître pour éviter qu'un mot
        # répété domine tout).
        k1 = 1.2
        b = 0.75

        chunks_number = self.index["chunks_number"]
        avg_len = self.index["avg_len_chunks"]
        doc_frequency_dict = self.index["document_frequency"]
        all_chunks_data = self.index["all_chunks_data"]

        # Dictionnaire pour stocker les scores de chaque chunk (clé = index du chunk, valeur = score)
        scores = {}
        print(f"DEBUG - Nombre de chunks contenant 'openai' : {doc_frequency_dict.get('openai', 0)}")
        print(f"DEBUG - DF de 'configure' : {doc_frequency_dict.get('configure', 0)}")
        print(f"DEBUG - DF de 'server' : {doc_frequency_dict.get('server', 0)}")
        for i, chunk_data in enumerate(all_chunks_data):
            score = 0.0
            term_frequency_dict = chunk_data["term_frequency"]
            tokens_number = chunk_data["clean_tokens_number"]

            for query_token in clean_query_tokens:
                if query_token not in term_frequency_dict:
                    continue

                # est-ce que le mot est très présent dans le chunk?
                term_frequency_in_chunk = term_frequency_dict[query_token]
                # est-ce que ce mot est rare ou pas dans tout le vllm?
                chunk_count_containing_token = doc_frequency_dict.get(
                    query_token, 0)

                # Calcul de l'IDF de BM25
                # IDF = Inverse Document Frequency : donne un poids faible
                # aux mots fréquents = mots qu'on trouve partout
                # mais qui n'aident pas à trouver un fichier précis
                # un poids forts aux mots rares
                idf = math.log(
                    (chunks_number - chunk_count_containing_token + 0.5) / (
                        chunk_count_containing_token + 0.5) + 1.0
                        )
                if idf < 0:
                    idf = 0.0  # Parfois lissé à 0 si le mot est ultra-fréquent

                # Calcul du numérateur et dénominateur du TF BM25
                # = (term frequency pondéré)
                numerator = term_frequency_in_chunk * (k1 + 1)
                denominator = term_frequency_in_chunk + k1 * (1 - b + b * (
                    tokens_number / avg_len))

                # Ajout au score total du chunk pour ce mot
                score += idf * (numerator / denominator)

            scores[i] = score

        # Trier les chunks par score décroissant
        sorted_chunks_indices = sorted(scores, key=scores.get, reverse=True)

        top_k_results = []
        for i in sorted_chunks_indices[:k]:
            if scores[i] > 0:  # On ne garde que ceux qui ont un score pertinent (> 0)
                result_chunk = all_chunks_data[i].copy()
                result_chunk["bm25_score"] = scores[i]
                top_k_results.append(result_chunk)

        return top_k_results

