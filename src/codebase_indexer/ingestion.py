# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  ingestion.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/30 14:01:19 by stephanie       #+#    #+#               #
#  Updated: 2026/07/23 14:41:33 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #
"""Module for discovering and loading the vLLM repository files."""
from pathlib import Path
from typing import List
from src.errors import RagLoadError


class CorpusVllmCompiler():
    """Compiles the relevant source and documentation files from a repository.

    Attributes:
        raw_corpus_path (Path): The path to the root of the raw repository.
    """
    def __init__(self, raw_corpus_path: str) -> None:
        """Initialize the compiler with the repository path.

        Args:
            raw_corpus_path (str): The string path to the target repository.
        """
        self.raw_corpus_path = Path(raw_corpus_path)

    def compile_corpus(self) -> List[Path]:
        """Discover and return valid Python, Text and Markdown files.

        Returns:
            List[Path]: Paths to valid .py, .txt and .md files.

        Raises:
            RagLoadError: If the repository path does not exist
            or is not a directory.
        """
        if not self.raw_corpus_path.exists():
            raise RagLoadError(f"Repository path '{self.raw_corpus_path}' "
                               f"does not exist.")
        if not self.raw_corpus_path.is_dir():
            raise RagLoadError(f"Repository path '{self.raw_corpus_path}' "
                               f"is not a directory.")

        valid_paths = []

        for path in self.raw_corpus_path.rglob("*"):
            if any(part.startswith(".")
                   or part == "__pycache__" for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in [
                ".py", ".md", ".txt"
            ]:
                valid_paths.append(path)

        return valid_paths
