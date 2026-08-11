# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  evaluator.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/08/10 14:01:04 by stmaire         #+#    #+#               #
#  Updated: 2026/08/10 15:15:24 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import json
from pydantic import ValidationError
from pathlib import Path
from src.dataset import DataSetLoader
from src.core.models import StudentSearchResults
from src.core.errors import (
    RagCliArgumentError, RagLoadError, RagValidationError)


IOU_THRESHOLD = 0.05


class Evaluator:
    """Evaluate retrieval quality against the ground-truth dataset.

    The evaluator compares the student's retrieved sources against the
    annotated sources for each question and computes an average recall score.
    """

    @staticmethod
    def _compute_iou(
            a_start: int, a_end: int, b_start: int, b_end: int
            ) -> float:
        """Compute the intersection-over-union (IoU) of two 1D intervals.

        Args:
            a_start: Start index of the first interval.
            a_end: End index of the first interval.
            b_start: Start index of the second interval.
            b_end: End index of the second interval.

        Returns:
            The IoU value between the two intervals. Returns ``0.0`` when
            the intervals do not overlap or the union is empty.
        """
        intersection = max(0, min(a_end, b_end) - max(a_start, b_start))
        if intersection == 0:
            return 0.0
        union = (a_end - a_start) + (b_end - b_start) - intersection
        if union <= 0:
            return 0.0
        return intersection / union

    def run(
            self, student_search_results_path: str, dataset_path: str
            ) -> float:
        """Run the evaluation for a student's search results.

        Args:
            student_search_results_path: Path to the JSON file containing
                the student's retrieved sources.
            dataset_path: Path to the dataset used as the ground truth.

        Raises:
            RagCliArgumentError: If the student's result file is missing or
                invalid.
            RagLoadError: If the dataset cannot be loaded or contains no
                answerable questions.
            RagValidationError: If the student's JSON cannot be parsed into
                a ``StudentSearchResults`` model.

        Returns:
            The average recall at ``k`` for the evaluated questions.
        """
        loader = DataSetLoader()
        truth_dataset = loader.dataset_load(dataset_path)

        try:
            student_path = Path(student_search_results_path)
            if not student_path.exists() or not student_path.is_file():
                raise RagCliArgumentError(
                    f"{student_path} does not exist or is not a file.")
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
            raise RagLoadError(
                f"Invalid JSON in {student_search_results_path}")
        except ValidationError as e:
            raise RagValidationError(
                path_name=student_search_results_path,
                pydantic_error=e
            )

        truth_map = {}
        for question in truth_dataset.rag_questions:
            if not hasattr(question, "sources") or not question.sources:
                continue
            truth_map[question.question_id] = [
                (s.file_path, s.first_character_index, s.last_character_index)
                for s in question.sources
            ]

        if not truth_map:
            raise RagLoadError(
                f"Cannot evaluate. "
                f"There is no answered question in {dataset_path}.")

        total_recall = 0.0
        queries_evaluated = 0
        k_value = student_search_results.k

        for result in student_search_results.search_results:
            if result.question_id not in truth_map:
                continue

            truth_chunks = truth_map[result.question_id]
            if not truth_chunks:
                continue

            limited_sources = result.retrieved_sources[:k_value]

            matched = 0
            for t_path, t_start, t_end in truth_chunks:
                for source in limited_sources:
                    if source.file_path != t_path:
                        continue
                    iou = self._compute_iou(
                        t_start, t_end,
                        source.first_character_index,
                        source.last_character_index
                    )
                    if iou >= IOU_THRESHOLD:
                        matched += 1
                        break

            question_recall = matched / len(truth_chunks)
            total_recall += question_recall

            queries_evaluated += 1

        if queries_evaluated == 0:
            return 0.0

        average_recall = total_recall / queries_evaluated

        print(f"Queries evaluated: {queries_evaluated}")
        print("\nEvaluation results")
        print(
            f"** Average Recall@{k_value} : {average_recall * 100:.2f}% **\n")

        return average_recall
