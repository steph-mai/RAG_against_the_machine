import fire
from functools import wraps
from src.utils.logger import logger
from src.search_data_set import SearchDataSet
from src.errors import RagCliArgumentError, RagError
from src.codebase_indexer.indexer import DocIndexer
from src.retriever import BM25Retriever
from src.evaluator import Evaluator


def handle_cli_errors(function) -> callable:
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RagError as e:
            logger.error(e)
        except Exception as e:
            logger.error(f"[CRITICAL ERROR] Unexpected error: {e}")
    return wrapper


class RAGCli:
    @handle_cli_errors
    def index(self, max_chunk_size: int = 2000, with_embeddings: bool = False
              ) -> None:
        """Ingest data/raw/ and build the index under data/processed/."""
        if max_chunk_size <= 0:
            raise RagCliArgumentError(
                "max_chunk_size must be a positive integer.")

        indexer = DocIndexer(max_chunk_size=max_chunk_size)
        indexer.build_and_save_index(
            with_embeddings=with_embeddings)

    @handle_cli_errors
    def search(self, query: str, k: int) -> str:
        """Return the top-k sources for a single query."""
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")

        retriever = BM25Retriever()
        retrieved_chunks = retriever.search(query, k)

        results = []
        for chunk_data in retrieved_chunks:
            file_path = chunk_data["file_path"]
            start_index = chunk_data["first_character_index"]
            end_index = chunk_data["last_character_index"]
            results.append(f"{file_path} [{start_index}:{end_index}]")

        # Fire affichera cette chaîne renvoyée proprement dans le terminal
        return "\n".join(results)

    @handle_cli_errors
    def search_dataset(self, dataset_path: str, k: int, save_directory: str, hybrid: bool = False) -> None:
        """Run search over a whole dataset and write a StudentSearchResults JSON file."""
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")

        if hybrid:
            from src.hybrid_retriever import HybridRetriever
            retriever = HybridRetriever()

        else:
            from src.retriever import BM25Retriever
            retriever = BM25Retriever()

        searcher = SearchDataSet(retriever=retriever)
        output_file = searcher.run(dataset_path, k, save_directory)

        print(f"Saved student_search_results to {output_file}")

    @handle_cli_errors
    def answer(self, query: str, k: int):
        """Answer a single query using the retrieved context."""
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")

        # Logique à implémenter plus tard avec le LLM
        pass

    @handle_cli_errors
    def answer_dataset(self, student_search_results_path: str, save_directory: str) -> None:
        """Generate answers for a dataset, producing a StudentSearchResultsAndAnswer JSON file."""
        if not student_search_results_path:
            raise RagCliArgumentError("Give a valid student_search_results_path.")
        if not save_directory:
            raise RagCliArgumentError("Give a valid save_directory.")

        # Logique à implémenter plus tard...
        # A la fin de ton traitement, tu devras print :
        # print(f"Saved student_search_results_and_answer to {output_file}")

    @handle_cli_errors
    def evaluate(
        self, student_search_results_path: str, dataset_path: str
        ) -> None:
        """Report your own recall@k against a ground-truth dataset."""
        if not student_search_results_path:
            raise RagCliArgumentError(
                "Give a valid student_search_results_path.")
        if not dataset_path:
            raise RagCliArgumentError("Give a valid dataset_path.")

        evaluator = Evaluator()
        evaluator.run(
            student_search_results_path=student_search_results_path,
            dataset_path=dataset_path
        )


if __name__ == "__main__":
    fire.Fire(RAGCli)
