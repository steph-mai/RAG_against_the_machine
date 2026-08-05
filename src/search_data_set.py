from tqdm import tqdm
import json
from src.retriever import BM25Retriever
from src.hybrid_retriever import HybridRetriever
from src.models import StudentSearchResults, MinimalSource, MinimalSearchResults
from src.dataset_loader import DataSetLoader
from pathlib import Path
from src.errors import RagCliArgumentError


class SearchDataSet:
    def __init__(
            self, retriever: BM25Retriever | HybridRetriever):
        self.retriever = retriever

    def _create_required_directory(
            self,
            dataset_path: str,
            save_directory: str = "data/output/search_results"
            )-> None:
        
    def run(
        self,
        dataset_path: str,
        k: int,
        save_directory: str = "data/output/search_results"
    ) -> Path:
        loader = DataSetLoader()
        dataset_model = loader.dataset_load(dataset_path)

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

        output_file = output_dir / dataset_name

        with open(file=output_file, mode="w", encoding="utf-8") as f:
            json.dump(
                final_results.model_dump(), f, ensure_ascii=False, indent=4)
        return output_file
