# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/01 09:37:31 by stmaire         #+#    #+#               #
#  Updated: 2026/08/06 11:08:29 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #
"""Module defining the chunking strategies for different file types."""

from abc import ABC, abstractmethod
from typing import List

from src.core.models import MinimalSource


class Chunker(ABC):
    """Abstract base class for document chunking strategies."""

    def chunk(
        self,
        content: str,
        file_path: str,
        max_size: int,
    ) -> List[MinimalSource]:
        """Split content into chunks.

        Args:
            content: The raw text content of the file.
            file_path: The relative path of the file.
            max_size: The maximum character size for each chunk.

        Returns:
            A list of chunk metadata objects.
        """
        chunks_list: List[MinimalSource] = []

        overlap: int = max_size // 10
        lines: str = content.splitlines(keepends=True)

        start_index: int = 0
        current_chunk_length: int = 0

        state = self._init_state()

        def _append_and_clear_buffer() -> None:
            """Append the buffer to the chunk list and reset it."""
            nonlocal current_chunk_length, start_index
            if current_chunk_length > 0:
                actual_length = min(current_chunk_length, max_size)
                chunks_list.append(
                    MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index,
                        last_character_index=start_index + actual_length,
                    )
                )
                start_index += current_chunk_length
                current_chunk_length = 0

        for line in lines:
            line_length = len(line)

            if line_length > max_size:
                _append_and_clear_buffer()

                line_start_idx = start_index
                for index in range(0, line_length, max_size):
                    line_slice = line[index:index + max_size]
                    slice_len = len(line_slice)

                    chunks_list.append(MinimalSource(
                        file_path=file_path,
                        first_character_index=line_start_idx + index,
                        last_character_index=line_start_idx + index + slice_len
                    ))
                start_index += line_length
                continue

            if self._should_cut(line, current_chunk_length, max_size, state):
                _append_and_clear_buffer()

            if current_chunk_length + line_length > max_size:
                chunks_list.append(MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                ))
                actual_overlap = min(overlap, current_chunk_length)
                start_index += current_chunk_length - actual_overlap
                current_chunk_length = actual_overlap

            current_chunk_length += line_length

        _append_and_clear_buffer()

        return chunks_list

    def _init_state(self) -> dict[str | None, bool | None]:
        """Initialize the chunker-specific parsing state.

        Returns:
            An empty state dictionary for the chunking strategy.
        """
        state = {}
        return state

    @abstractmethod
    def _should_cut(
        self,
        line: str,
        current_chunk_length: int,
        max_size: int,
        state: dict | None,
    ) -> bool:
        """Determine whether a line should force a chunk cut.

        Args:
            line: The current line being inspected.
            current_chunk_length: The number of characters in the chunk.
            max_size: The maximum allowed size for a chunk.
            state: Mutable parser state shared across lines.

        Returns:
            True if the current line should start a new chunk, otherwise False.
        """
        pass


class TxtChunker(Chunker):
    """Chunker specialized for plain text files."""

    MIN_FILL_TO_CUT_IF_EMPTY_LINE = 0.5

    def _should_cut(
        self,
        line: str,
        current_chunk_length: int,
        max_size: int,
        state: dict | None,
    ) -> bool:
        """Determine whether an empty line should trigger a chunk cut.

        Args:
            line: The current line being inspected.
            current_chunk_length: The current length of the chunk buffer.
            max_size: The maximum allowed size for a chunk.
            state: Mutable parser state shared across lines.

        Returns:
            True if the chunk should be cut before continuing, otherwise False.
        """
        return not line.strip() and current_chunk_length > (
            self.MIN_FILL_TO_CUT_IF_EMPTY_LINE * max_size
        )


class PyChunker(Chunker):
    """Chunker specialized for Python source files."""

    MIN_FILL_TOP_LEVEL = 0.20
    MIN_FILL_METHOD = 0.85
    MIN_FILL_BLOCK = 0.95

    def _init_state(self):
        """Initialize Python-specific parsing state.

        Returns:
            A state dictionary tracking decorator blocks.
        """
        return {"is_in_decorator_block": False}

    def _should_cut(
        self,
        line: str,
        current_chunk_length: int,
        max_size: int,
        state: dict | None,
    ) -> bool:
        """Determine whether a Python line should force a chunk cut.

        Args:
            line: The current line being inspected.
            current_chunk_length: The current length of the chunk buffer.
            max_size: The maximum allowed size for a chunk.
            state: Mutable parser state shared across lines.

        Returns:
            True if the chunk should be cut before continuing, otherwise False.
        """
        stripped_line = line.lstrip()
        if not stripped_line:
            return False

        indentation = len(line) - len(stripped_line)
        is_def_or_class = stripped_line.startswith((
            "def ", "class ", "async def "))
        is_decorator = stripped_line.startswith("@")
        is_block = stripped_line.startswith(
            ("if ", "for ", "while ", "with ", "try:", "except ")
        )

        should_cut = False

        if indentation == 0:
            if is_def_or_class or is_decorator:
                if not state["is_in_decorator_block"] and (
                    current_chunk_length > (max_size * self.MIN_FILL_TOP_LEVEL)
                ):
                    should_cut = True
                state["is_in_decorator_block"] = is_decorator
            else:
                state["is_in_decorator_block"] = False

        elif indentation == 4:
            if is_def_or_class or is_decorator:
                if not state["is_in_decorator_block"] and (
                    current_chunk_length > (max_size * self.MIN_FILL_METHOD)
                ):
                    should_cut = True
                state["is_in_decorator_block"] = is_decorator
            else:
                state["is_in_decorator_block"] = False

        elif indentation >= 8:
            if is_block and current_chunk_length > (
                max_size * self.MIN_FILL_BLOCK
            ):
                should_cut = True

        return should_cut


class MdChunker(Chunker):
    """Chunker specialized for Markdown files."""

    MIN_THRESHOLD_TO_CUT_IF_H1 = 0.1
    MIN_THRESHOLD_TO_CUT_IF_H2 = 0.7
    MIN_THRESHOLD_TO_CUT_IF_EMPTY_LINE = 0.8

    def _init_state(self):
        """Initialize Markdown-specific parsing state.

        Returns:
            A state dictionary tracking whether the parser is inside
            a code block.
        """
        return {"is_in_code_block": False}

    def _should_cut(
        self,
        line: str,
        current_chunk_length: int,
        max_size: int,
        state: dict | None,
    ) -> bool:
        """Determine whether a Markdown line should force a chunk cut.

        Args:
            line: The current line being inspected.
            current_chunk_length: The current length of the chunk buffer.
            max_size: The maximum allowed size for a chunk.
            state: Mutable parser state shared across lines.

        Returns:
            True if the chunk should be cut before continuing, otherwise False.
        """
        stripped_line = line.lstrip()

        if stripped_line.startswith("```"):
            state["is_in_code_block"] = not state["is_in_code_block"]
            return False
        if state["is_in_code_block"]:
            return False
        if stripped_line.startswith("# ") and current_chunk_length > int(
            max_size * self.MIN_THRESHOLD_TO_CUT_IF_H1
        ):
            return True
        if stripped_line.startswith(("## ", "!!! ")) and (
            current_chunk_length > int(
                max_size * self.MIN_THRESHOLD_TO_CUT_IF_H2)
        ):
            return True

        if not stripped_line and current_chunk_length > int(
            self.MIN_THRESHOLD_TO_CUT_IF_EMPTY_LINE * max_size
        ):
            return True
        return False
