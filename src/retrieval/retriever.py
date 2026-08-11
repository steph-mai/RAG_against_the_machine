from abc import ABC, abstractmethod
from typing import Any, List, Dict


class Retriever(ABC):
    """Abstract base class for all retrieval engines in the RAG pipeline."""

    @abstractmethod
    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Execute a search query and return the top-k relevant chunks.

        Args:
            query (str): The search query string.
            top_k (int): The maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: A list of chunk dictionaries matching
            the query.
        """
        pass
