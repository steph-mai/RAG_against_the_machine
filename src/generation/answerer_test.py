from typing import List, Dict, Any
from src.retrieval.retriever import Retriever
from src.core.models import StudentSearchResultsAndAnswer, MinimalAnswer, MinimalSource

class Answerer:
    """Handles context retrieval and answer generation using Qwen/Qwen3-0.6B."""

    def __init__(self, retriever: Retriever, llm_client_or_model):
        """
        Args:
            retriever: An instance of a class inheriting from Retriever (BM25 or Hybrid).
            llm_client_or_model: Ton instance ou client pour interroger Qwen/Qwen3-0.6B.
        """
        self.retriever = retriever
        self.llm = llm_client_or_model

    def _format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formate les chunks récupérés pour les injecter dans le prompt du LLM."""
        context_str = ""
        for i, chunk in enumerate(retrieved_chunks):
            file_path = chunk.get("file_path", "unknown")
            content = chunk.get("content", "")
            context_str += f"--- Source [{i+1}]: {file_path} ---\n{content}\n\n"
        return context_str

    def generate_answers_for_dataset(self, queries_data: List[Dict[str, Any]], k: int) -> StudentSearchResultsAndAnswer:
        """
        Génère les réponses pour une liste de questions de test.

        Args:
            queries_data: Liste contenant les dictionnaires de questions (ex: [{'question_id': 'q1', 'question': '...'}])
            k: Nombre de chunks à récupérer par question.
        """
        search_results_list = []

        for item in queries_data:
            q_id = item["question_id"]
            question = item["question"]

            retrieved_chunks = self.retriever.search(query=question, top_k=k)

            minimal_sources = []
            for chunk in retrieved_chunks:
                minimal_sources.append(
                    MinimalSource(
                        file_path=chunk["file_path"],
                        first_character_index=chunk["first_character_index"],
                        last_character_index=chunk["last_character_index"]
                    )
                )

            context = self._format_context(retrieved_chunks)

            prompt = (
                f"Based strictly on the following context, answer the user's question clearly and concisely.\n\n"
                f"Context:\n{context}\n"
                f"Question: {question}\n"
                f"Answer:"
            )

            answer_text = "To configure..." # Remplacer par l'appel réel au LLM

            minimal_answer = MinimalAnswer(
                question_id=q_id,
                question=question,
                retrieved_sources=minimal_sources,
                answer=answer_text
            )
            search_results_list.append(minimal_answer)

        # 6. Retourne le modèle global demandé par le sujet
        return StudentSearchResultsAndAnswer(
            search_results=search_results_list,
            k=k
        )
