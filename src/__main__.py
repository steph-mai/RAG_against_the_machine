import fire
from pathlib import Path
from src.models import StudentSearchResults, StudentSearchResultsAndAnswer


class RAGCli():
    def index(self, max_chunk_size: int = 2000):
        if max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be a positive integer.")
            # Ingest data/raw/ and build the index under data/processed/.
        try:
            return max_chunk_size
        except Exception as e:
            print(f"Indexation error {e}")

    def search(self, query: str, k: int):
        # Return the top-k sources for a single query.
        if not query:
            raise ValueError("There is no query.")
        if k <= 0:
            raise ValueError("k must be a positive integer.")
        return query

    def search_dataset(self, dataset_path: Path, k: int, save_directory: str) -> StudentSearchResults:
        # Run search over a whole dataset and write a StudentSearchResults JSON file.
        return save_directory

    def answer(self, query: str, k: int):
        # Answer a single query using the retrieved context.
        return k

    def answer_dataset(student_search_results_path: Path, save_directory: str) -> StudentSearchResultsAndAnswer:
        # Generate answers for a dataset, producing a StudentSearchResultsAndAnswer JSON file.
        pass

    def evaluate(student_search_results_path: Path, dataset_path: Path):
        # Report your own recall@k against a ground-truth dataset, for your own testing
        pass


if __name__ == "__main__":
    fire.Fire(RAGCli)
