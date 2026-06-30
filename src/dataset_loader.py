# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  dataset_loader.py                                 :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/30 11:39:10 by stephanie       #+#    #+#               #
#  Updated: 2026/06/30 11:59:39 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import json
from pathlib import Path
from src.models import RagDataset
from pydantic import ValidationError
from src.errors import RagLoadError, RagValidationError


class Dataset_loader:
    def dataset_load(self, file_path: str) -> RagDataset:
        """
        Loads a JSON dataset.
        Handles cases: unsupported file type, missing file, permission
        error, invalid JSON, empty file and invalid data structure.
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
        except json.JSONDecodeError(content) as e:
            raise RagLoadError(f"Invalid JSON in '{path.name}."
                               f"Line {e.lineno}, {e.colno}.")
        except ValidationError as e:
            raise RagValidationError(path.name, e)
