import json
from pathlib import Path
from src.dataset_loader import DataSetLoader
from src.search_data_set import SearchDataSet
from src.models import StudentSearchResults
from src.errors import RagCliArgumentError, RagLoadError, RagValidationError

class Evaluator:
    def run(
            self, student_search_results_path: str, dataset_path: str) -> float:
        loader = DataSetLoader
        truth_dataset = loader.dataset_load(dataset_path)

        try:
            student_path = Path(student_search_results_path)
            if not student_path.exists() or not student_path.is_file():
                raise RagCliArgumentError(f"{student_path} does not exist or is not a file.")
        except PermissionError:
            raise RagCliArgumentError(f"Permission denied for {student_path}")

        try:
            with open(
                file=student_search_results_path,
                mode="r",
                encoding="utf-8"
            ) as f:
                student_data_dict = json.load(f)
                student_search_results = StudentSearchResults(
                    **student_data_dict)
        except json.JSONDecodeError:
            raise RagLoadError(f"Invalid JSON in {student_search_results_path}")
        except Exception as e:
            raise RagValidationError(
                f"Error pydantic in {student_search_results_path}: {e}")

        truth_map = {}
        for question in truth_dataset.rag_questions:
            if not hasattr(question, "sources"):
                continue
            truth_map[question.question_id] = {
                s.file_path for s in question.sources}
        if not truth_map:
            raise RagLoadError(
                f"Cannot evaluate. "
                f"There is no answered question in {dataset_path}.")

        total_recall = 0.0
        queries_evaluated = 0

        for result in student_search_results.search_results:
            if result.question_id not in truth_map:
                continue
            truth_file_paths = truth_map[question.question_id]

            if not truth_file_paths:
                continue

            retrieved_paths = {
                source.file_path for source in result.retrieved_sources}

            intersection = (
                truth_map[question.question_id].intersection(retrieved_paths))
            recall = len(intersection) / len(truth_map[question.question_id])

            total_recall += recall
            queries_evaluated += 1

            if queries_evaluated == 0:
                return 0.0

            average_recall = total_recall / queries_evaluated
            k_value = student_search_results.k

            # TODO display subject
            print("\nEvaluation results")
            print(f"** Average Recall@{k_value} : {average_recall * 100:.2f}% **\n")







