from tqdm import tqdm
import json
from src.retrieval import BM25Retriever
from src.retrieval import HybridRetriever
from src.core.models import (
    StudentSearchResults, MinimalSource, MinimalSearchResults)
from src.dataset import DataSetLoader
from pathlib import Path
from src.core.errors import RagCliArgumentError


class SearchDataSet:
    """Manage dataset search execution and save minimal search results.

    This class wraps a BM25 or hybrid retriever and exports the search results
    for a dataset into a JSON file.

    Args:
        retriever: Retriever used to perform the search queries.
    """

    def __init__(
            self, retriever: BM25Retriever | HybridRetriever):
        """Initialize the dataset search executor.

        Args:
            retriever: Retriever used to perform the search queries.
        """
        self.retriever = retriever

    def _create_required_dir(
            self,
            dataset_path: str,
            save_directory: str = "data/output/search_results"
            ) -> Path:
        """Create the output directory and return the target file path.

        Args:
            dataset_path: Path to the dataset file.
            save_directory: Base directory where results are saved.

        Returns:
            Path to the JSON output file.

        Raises:
            RagCliArgumentError: If the directory cannot be created because of
                permissions or an OS-level failure.
        """
        dataset_name = Path(dataset_path).name

        dataset_folder_name = Path(dataset_path).parent.name

        output_dir = Path(save_directory)
        if dataset_folder_name and dataset_folder_name not in output_dir.parts:
            output_dir = output_dir / dataset_folder_name

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise RagCliArgumentError(
                f"Permission denied. "
                f"Cannot create directory at {output_dir}")
        except OSError as e:
            raise RagCliArgumentError(
                f"Failed to create directory "
                f"at {output_dir}. Details: {e}")

        output_file = output_dir / dataset_name

        return output_file

    def run(
        self,
        dataset_path: str,
        k: int,
        save_directory: str = "data/output/search_results"
    ) -> Path:
        """Run the search pipeline on a dataset and save the results.

        Args:
            dataset_path: Path to the dataset file to search.
            k: Number of retrieved sources per question.
            save_directory: Base directory used to store the output file.

        Returns:
            Path to the saved JSON file.
        """
        loader = DataSetLoader()
        dataset_model = loader.dataset_load(dataset_path)

        output_file = self._create_required_dir(
            dataset_path, save_directory)

        all_minimal_search_results = []

        for rag_question in tqdm(
            dataset_model.rag_questions,
            desc="Searching dataset",
            unit="query"
        ):
            if not rag_question.question:
                search_result = MinimalSearchResults(
                    question_id=rag_question.question_id,
                    question="",
                    retrieved_sources=[]
                )
                all_minimal_search_results.append(search_result)
                continue

            question_id = rag_question.question_id
            question = rag_question.question

            raw_question_results = self.retriever.search(question, k)

            retrieved_sources = []

            for result in raw_question_results:
                source = MinimalSource(
                    file_path=result["file_path"],
                    first_character_index=result["first_character_index"],
                    last_character_index=result["last_character_index"]
                )
                retrieved_sources.append(source)

            search_result = MinimalSearchResults(
                question_id=question_id,
                question=question,
                retrieved_sources=retrieved_sources
            )
            all_minimal_search_results.append(search_result)

        final_results = StudentSearchResults(
            search_results=all_minimal_search_results, k=k)

        with open(file=output_file, mode="w", encoding="utf-8") as f:
            json.dump(
                final_results.model_dump(), f, ensure_ascii=False, indent=4)
        return output_file
