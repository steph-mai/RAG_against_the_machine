import fire
from functools import wraps
from pathlib import Path
from src.models import StudentSearchResults, StudentSearchResultsAndAnswer
from src.utils.logger import logger
from src.errors import RagCliArgumentError, RagError
from src.indexer import DocIndexer


def handle_cli_errors(function) -> callable:
    @wraps(function)
    # permet de conserver les métadonnées de la function
    def wrapper(*args, **kwargs):
        # création d'un "garde du corps qui accepte toutes les fonctions
        try:
            return function(*args, **kwargs)
        # demande à  la fonction de s'exécuter
        except RagError as e:
            logger.error(e)
        except Exception as e:
            logger.error(f"[CRITICAL ERROR] Unexpected error: {e}")
        # c'est lui qui récupère les erreurs.
    return wrapper
    # on renvoie un garde du corps prêt à agir.


class RAGCli():
    @handle_cli_errors
    def index(self, max_chunk_size: int = 2000) -> Path:
        # Ingest data/raw/ and build the index under data/processed/.
        if max_chunk_size <= 0:
            raise RagCliArgumentError(
                "max_chunk_size must be a positive integer.")
        # gerer le déroulé de l'indexation avec tqdm dans la classe Indexer
        indexer = DocIndexer(max_chunk_size=2000)
        index_path: Path = indexer.build_and_save_index()
        return index_path

    @handle_cli_errors
    def search(self, query: str, k: int):
        # Return the top-k sources for a single query.
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")
        return query

    @handle_cli_errors
    def search_dataset(
            self, dataset_path: str, k: int, save_directory: str
            ) -> StudentSearchResults:
        # Run search over a whole dataset and write a
        # StudentSearchResults JSON file.
        if not dataset_path:
            raise RagCliArgumentError("Give a valid dataset_path.")
        if not save_directory:
            raise RagCliArgumentError("Give a valid save_directory.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")
        return save_directory

    @handle_cli_errors
    def answer(self, query: str, k: int):
        # Answer a single query using the retrieved context.
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")
        return k

    @handle_cli_errors
    def answer_dataset(
            self, student_search_results_path: str, save_directory: str
            ) -> StudentSearchResultsAndAnswer:
        # Generate answers for a dataset, producing a
        # StudentSearchResultsAndAnswer JSON file.
        if not student_search_results_path:
            raise RagCliArgumentError(
                "Give a valid student_search_results_path.")
        if not save_directory:
            raise RagCliArgumentError("Give a valid save_directory.")
        return save_directory

    @handle_cli_errors
    def evaluate(self, student_search_results_path: str, dataset_path: str):
        # Report your own recall@k against a ground-truth dataset,
        # for your own testing
        if not student_search_results_path:
            raise RagCliArgumentError(
                "Give a valid student_search_results_path.")
        if not dataset_path:
            raise RagCliArgumentError("Give a valid dataset_path.")
        return dataset_path


if __name__ == "__main__":
    fire.Fire(RAGCli)
