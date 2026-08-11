from functools import wraps
from typing import Any, Callable

from src.indexing import DocIndexer
from src.core.errors import RagCliArgumentError, RagError
from src.core.formatters import Formatter
from src.dataset.evaluator import Evaluator
from src.retrieval import BM25Retriever, HybridRetriever
from src.generation.answerer import Answerer
from src.dataset.search_data_set import SearchDataSet
from src.core.logger import logger


def handle_cli_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a CLI command and log expected errors consistently.

    Args:
        function: The CLI handler function to wrap.

    Returns:
        A wrapped function that catches `RagError` and unexpected exceptions.
    """
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Call the wrapped CLI command and handle errors.

        Args:
            *args: Positional arguments forwarded to the wrapped function.
            **kwargs: Keyword arguments forwarded to the wrapped function.

        Returns:
            The wrapped function result, if any.
        """
        try:
            return function(*args, **kwargs)
        except RagError as e:
            logger.error(e)
        except Exception as e:
            logger.error(f"[CRITICAL ERROR] Unexpected error: {e}")

    return wrapper


class RAGCli:
    """
    Command-line interface for indexing, searching, answering and evaluating.
    """

    @handle_cli_errors
    def index(
        self,
        max_chunk_size: int = 2000,
        with_embeddings: bool = False,
    ) -> None:
        """Ingest data/raw and build the processed index.

        Args:
            max_chunk_size: Maximum number of characters allowed per chunk.
            with_embeddings: Whether to also populate a ChromaDB vector index.

        Returns:
            None
        """
        if max_chunk_size <= 10:
            raise RagCliArgumentError(
                "max_chunk_size must be higher or equal to 10.")
        if max_chunk_size > 2000:
            raise RagCliArgumentError(
                "max_chunk_size can not be higher than 2000 "
                "(moulinette max_context_length)."
            )

        indexer = DocIndexer(max_chunk_size=max_chunk_size)
        indexer.build_and_save_index(with_embeddings=with_embeddings)

    @handle_cli_errors
    def search(self, query: str, k: int = 10, hybrid: bool = False) -> str:
        """Return the top-k sources for a single query.

        Args:
            query: The user query to search.
            k: Number of results to return.
            hybrid: Whether to use the hybrid retriever instead of BM25.

        Returns:
            A newline-separated list of file paths and character ranges.
        """
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")

        retriever: BM25Retriever | HybridRetriever
        if hybrid:
            from src.retrieval import HybridRetriever
            retriever = HybridRetriever()
        else:
            retriever = BM25Retriever()

        retrieved_chunks = retriever.search(query, k)

        results = []
        for chunk_data in retrieved_chunks:
            file_path = chunk_data["file_path"]
            start_index = chunk_data["first_character_index"]
            end_index = chunk_data["last_character_index"]
            results.append(f"{file_path} [{start_index}:{end_index}]")

        return "\n".join(results)

    @handle_cli_errors
    def search_dataset(
        self,
        dataset_path: str = (
            "data/datasets/UnansweredQuestions/dataset_docs_public.json"),
        k: int = 10,
        save_directory: str = "data/output/search_results/UnansweredQuestions",
        hybrid: bool = False,
    ) -> None:
        """Run search over a whole dataset and save the results.

        Args:
            dataset_path: Path to the dataset file.
            k: Number of results to retrieve per query.
            save_directory: Directory where the result file will be written.
            hybrid: Whether to use the hybrid retriever instead of BM25.

        Returns:
            None
        """
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")

        retriever: BM25Retriever | HybridRetriever
        if hybrid:
            from src.retrieval import HybridRetriever
            retriever = HybridRetriever()
        else:
            retriever = BM25Retriever()

        searcher = SearchDataSet(retriever=retriever)
        output_file = searcher.run(dataset_path, k, save_directory)

        logger.info(f"Saved student_search_results to {output_file}")

    @handle_cli_errors
    def answer(self, query: str, k: int = 10, hybrid: bool = False) -> None:
        """Answer a single query using the retrieved context.

        Args:
            query: The user query to answer.
            k: Number of retrieved chunks to use as context.
            hybrid: Whether to use the hybrid retriever instead of BM25.

        Returns:
            None
        """
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")

        retriever: BM25Retriever | HybridRetriever
        if hybrid:
            from src.retrieval import HybridRetriever
            retriever = HybridRetriever()
        else:
            retriever = BM25Retriever()

        retrieved_chunks = retriever.search(query, top_k=k)

        answerer = Answerer()
        generated_answer = answerer.generate_answer(
            question_id="query_1",
            query=query,
            retrieved_chunks=retrieved_chunks)

        formatter = Formatter()
        formatter.print_answer(generated_answer)

    @handle_cli_errors
    def answer_dataset(
        self,
        student_search_results_path: str = "data/output/search_results/"
        "UnansweredQuestions/dataset_docs_public.json",
        save_directory: str = "data/output/search_results_and_answer/"
        "UnansweredQuestions",
    ) -> None:
        """Generate answers for a dataset and save the result file.

        Args:
            student_search_results_path: Path to the search results file.
            save_directory: Directory where the answer file will be written.

        Returns:
            None
        """
        if not save_directory:
            raise RagCliArgumentError("Give a valid save_directory.")

        answerer = Answerer()
        output_file = answerer.run(
            student_search_results_path=student_search_results_path,
            save_directory=save_directory
        )

        logger.info(
            f"Saved student_search_results_and_answer to {output_file}")

    @handle_cli_errors
    def evaluate(
        self,
        student_search_results_path: str = "data/output/search_results/"
        "UnansweredQuestions/dataset_docs_public.json",
        dataset_path: str = "data/datasets/AnsweredQuestions/"
        "dataset_docs_public.json",
    ) -> None:
        """Report recall@k against a ground-truth dataset.

        Args:
            student_search_results_path: Path to the search results file.
            dataset_path: Path to the evaluation dataset.

        Returns:
            None
        """
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
