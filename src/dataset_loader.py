# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  dataset_loader.py                                 :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/30 11:39:10 by stephanie       #+#    #+#               #
#  Updated: 2026/08/05 14:10:58 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import json
from pathlib import Path
from src.models import RagDataset
from pydantic import ValidationError
from src.errors import RagLoadError, RagValidationError


class DataSetLoader:
    def dataset_load(self, file_path: str) -> RagDataset:
        """
        Loads a JSON dataset into a RagDataset model.

        Handles various error cases such as unsupported file type,
        missing files, permission errors, and invalid data structures.

        Args:
            file_path (str): The path to the JSON dataset file.

        Returns:
            RagDataset: The validated dataset containing the questions.

        Raises:
            RagLoadError: If the file is missing, empty, or unreadable.
            ValueError: If the file type is not .json.
            RagValidationError: If the JSON structure does not match
            the Pydantic models.
        """
        path = Path(file_path)

        if not path.exists():
            raise RagLoadError(f"Missing file: '{path.name}' not found.")

        if path.suffix.lower() != ".json":
            raise ValueError(f"Invalid file type : '{path.suffix}'. "
                             f"Please provide a .json file")
        if path.is_dir():
            raise RagLoadError(f"Excepted a file but {path.name} is a "
                               f"directory.")

        try:
            with open(path, mode="r", encoding="utf-8") as f:
                content = f.read().strip()
        except PermissionError:
            raise RagLoadError(f"You dont't have permission for the "
                               f"directory {path.parent} or for the file "
                               f"{path.name}")

        if not content:
            raise RagLoadError(f"File '{path.name}' is empty.")

        try:
            dataset_dict = json.loads(content)
            ragdataset = RagDataset(**dataset_dict)
            return ragdataset
        except json.JSONDecodeError as e:
            raise RagLoadError(f"Invalid JSON in '{path.name}."
                               f"Line {e.lineno}, {e.colno}.")
        except ValidationError as e:
            raise RagValidationError(path.name, e)
