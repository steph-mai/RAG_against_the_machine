# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/01 09:37:31 by stmaire         #+#    #+#               #
#  Updated: 2026/07/27 09:11:58 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #
"""Module defining the chunking strategies for different file types."""
from abc import abstractmethod, ABC
from src.models import MinimalSource
from typing import List


class Chunker(ABC):
    """Abstract base class for document chunking strategies."""

    def chunk(
            self,
            content: str,
            file_path: str,
            max_size: int,
            ) -> List[MinimalSource]:
        """Base method to split content into chunks.

        Args:
            content (str): The raw text content of the file.
            file_path (str): The relative path of the file.
            max_size (int): The maximum character size for each chunk.

        Returns:
            List[MinimalSource]: A list of type-safe chunk metadata.
        """

        chunks_list: List[MinimalSource] = []

        overlap: int = max_size // 10
        lines: str = content.splitlines(keepends=True)

        start_index: int = 0
        current_chunk_length: int = 0

        state = self._init_state()

        def append_and_clear_buffer() -> None:
            nonlocal current_chunk_length, start_index
            if current_chunk_length > 0:
                chunks_list.append(MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                ))
                start_index += current_chunk_length
                current_chunk_length = 0

        for line in lines:
            line_length = len(line)

            if line_length > max_size:
                append_and_clear_buffer()

                for index in range(0, line_length, max_size):
                    line_slice = line[index:index + max_size]
                    chunks_list.append(MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index + index,
                        last_character_index=start_index + index + len(
                            line_slice)
                    ))
                start_index += line_length
                continue

            if self._should_cut(line, current_chunk_length, max_size, state):
                append_and_clear_buffer()

            if current_chunk_length + line_length > max_size:
                if current_chunk_length > 0:
                    chunks_list.append(MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index,
                        last_character_index=start_index + current_chunk_length
                    ))
                    actual_overlap = min(overlap, current_chunk_length)
                    start_index += current_chunk_length - actual_overlap
                    current_chunk_length = actual_overlap
                else:
                    append_and_clear_buffer()

            current_chunk_length += line_length

        append_and_clear_buffer()

        return chunks_list

    def _init_state(self) -> dict[str | None, bool | None]:
        state = {}
        return state

    @abstractmethod
    def _should_cut(
        self,
        line: str,
        current_chunk_length: int,
        max_size: int,
        state: dict | None
    ) -> bool:
        pass


class TxtChunker(Chunker):

    MIN_FILL_TO_CUT_IF_EMPTY_LINE = 0.5

    def _should_cut(
        self, line: str, current_chunk_length: int,
        max_size: int, state: dict | None
    ) -> bool:
        return not line.strip() and current_chunk_length > (
                self.MIN_FILL_TO_CUT_IF_EMPTY_LINE * max_size)


class PyChunker(Chunker):

    MIN_FILL_TO_CUT_IF_BOUNDARY = 0.35

    def _init_state(self):
        return {"is_in_decorator_block": False}

    def _should_cut(
        self, line: str, current_chunk_length: int,
        max_size: int, state: dict | None
    ) -> bool:

        stripped_line = line.lstrip()
        indentation = len(line) - len(stripped_line)
        should_cut = False
        min_threshold = max_size * self.MIN_FILL_TO_CUT_IF_BOUNDARY
        is_boundary = stripped_line.startswith((
                "if TYPE_CHECKING:",
                "__all__", "if __name__"
            ))

        if indentation == 0:
            if stripped_line.startswith(("def ", "class ", "async def ")):
                if not state["is_in_decorator_block"] and (
                        current_chunk_length > min_threshold):
                    should_cut = True
                state["is_in_decorator_block"] = False

            elif stripped_line.startswith("@"):
                if not state["is_in_decorator_block"] and (
                        current_chunk_length > min_threshold):
                    should_cut = True
                state["is_in_decorator_block"] = True

            elif is_boundary:
                if not state["is_in_decorator_block"] and (
                        current_chunk_length > min_threshold):
                    should_cut = True
                state["is_in_decorator_block"] = False
        return should_cut


class MdChunker(Chunker):

    MIN_THRESHOLD_TO_CUT_IF_H1 = 0.1
    MIN_THRESHOLD_TO_CUT_IF_H2 = 0.7
    # MIN_THRESHOLD_TO_CUT_IF_LINK = 0.95
    MIN_THRESHOLD_TO_CUT_IF_EMPTY_LINE = 0.9

    def _init_state(self):
        return {"is_in_code_block": False}

    def _should_cut(
        self, line: str, current_chunk_length: int,
        max_size: int, state: dict | None
    ) -> bool:

        stripped_line = line.lstrip()

        if stripped_line.startswith("```"):
            state["is_in_code_block"] = not state["is_in_code_block"]
            return False
        if state["is_in_code_block"]:
            return False
        if stripped_line.startswith(
                "# ") and current_chunk_length > int(
                    max_size * self.MIN_THRESHOLD_TO_CUT_IF_H1):
            return True
        if stripped_line.startswith(("## ", "!!! ")) and (
                current_chunk_length > int(
                    max_size * self.MIN_THRESHOLD_TO_CUT_IF_H2)):
            return True
        # if stripped_line.startswith(("[", "]", "(", ")", "{", "}")) and (
        #         current_chunk_length > int(
        #             max_size * self.MIN_THRESHOLD_TO_CUT_IF_LINK)):
        #     return True

        if not stripped_line and current_chunk_length > int(
                self.MIN_THRESHOLD_TO_CUT_IF_EMPTY_LINE * max_size):
            return True
        return False


# if __name__ == "__main__":
#     from pathlib import Path
#     from src.models import MinimalSource

#     path = Path("data/raw/vllm-0.10.1/docs/usage/v1_guide.md")
#     MAX_SIZE_LIMIT = 2000
#     file_path_str = str(path)

#     print("=" * 60)
#     print(f"ANALYSE ET DÉCOUPAGE DE : {path}")
#     print("=" * 60)

#     if not path.exists():
#         print(f"❌ Erreur : Le fichier '{path}' n'a pas été trouvé.")
#     else:
#         with open(path, mode="r", encoding="utf-8") as f:
#             real_content = f.read()

#         if path.suffix == ".py":
#             chunker = PyChunker()

#         elif path.suffix == ".txt":
#             chunker = TxtChunker()

#         elif path.suffix == ".md":
#             chunker = MdChunker()

#         chunks = list(chunker.chunk(
#                 content=real_content,
#                 file_path=file_path_str,
#                 max_size=MAX_SIZE_LIMIT
#             ))

#         # 4. Affichage des statistiques globales (Validation)
#         total_chunks = len(chunks)
#         print(f"📊 Statistiques d'ingestion :")
#         print(f"   - Nombre total de caractères dans le fichier : {len(real_content)}")
#         print(f"   - Nombre de chunks générés : {total_chunks}")
#         print("-" * 60)

#         # 5. Affichage d'un échantillon (ex: les 3 premiers chunks)
#         for i, source in enumerate(chunks, 1):
#             extracted_text = real_content[source.first_character_index : source.last_character_index]

#             print(f"\n🔍 [ÉCHANTILLON] CHUNK N°{i}/{total_chunks}")
#             print(f"   Index caractères : [{source.first_character_index} -> {source.last_character_index}]")
#             print(f"   Taille du chunk : {len(extracted_text)} caractères")
#             print("." * 40)
#             # On affiche les 5 premières lignes pour inspecter le contenu visuellement
#             sample_lines = extracted_text.splitlines()[:5]
#             for line in sample_lines:
#                 # print(f"   | {line.endwith('\n') and line or line + '\n'}", end="")
#                 print(f"{line}")
#             if len(extracted_text.splitlines()) > 5:
#                 print("   | [... reste du contenu masqué ...]")
#             print("." * 40)

        # # 6. Vérification automatique des contraintes du sujet (Edge Cases)
        # print("\n🛡️ Vérification des contraintes du sujet :")
        # errors = 0
        # for idx, source in enumerate(chunks):
        #     chunk_txt = real_content[source.first_character_index : source.last_character_index]
        #     if len(chunk_txt) > MAX_SIZE_LIMIT:
        #         print(f"   ❌ Erreur au Chunk {idx+1} : Taille de {len(chunk_txt)} dépasse {MAX_SIZE_LIMIT} !")
        #         errors += 1

        # if errors == 0:
        #     print(f"   ✅ Parfait ! Tous les {total_chunks} chunks respectent la limite stricte de {MAX_SIZE_LIMIT} caractères.")


