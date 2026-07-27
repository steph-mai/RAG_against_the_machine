import json
from pathlib import Path
from src.dataset_loader import Dataset_loader
from src.search_data_set import StudentSearchResults, SearchDataSet
from src.models import StudentSearchResults
from src.errors import RagCliArgumentError, RagLoadError, RagValidationError

class Evaluator:
    def run(
            self, student_search_results_path: str, dataset_path: str) -> float:
        loader = Dataset_loader()
        truth_dataset = loader.dataset_load(dataset_path)

        try:
            student_path = Path(student_search_results_path)
            if not student_path.exists() or not student_path.is_file():
                raise RagCliArgumentError(f"{student_path} does not exist or is not a directory")
        except PermissionError:
            raise RagCliArgumentError(f"Permission denied for {student_path}")

        try:
            with open(
                file=student_search_results_path,
                mode="r",
                encoding="utf-8"
            ) as f:
                student_data_dict = json.load(f)
                student_search_results = StudentSearchResults(student_data_dict)
        except json.JSONDecodeError:
            raise RagLoadError(f"Invalid JSON in {student_search_results}")
        except Exception as e:
            raise RagValidationError(f"Error pydantic in {student_search_results_path}: {e}")

