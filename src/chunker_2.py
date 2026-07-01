
"""Module defining the chunking strategies for different file types."""
from abc import abstractmethod, ABC
from src.models import MinimalSource
from typing import Iterator


class Chunker(ABC):
    """Abstract base class for document chunking strategies."""

    def chunk(
            self,
            content: str,
            file_path: str,
            max_size: int,
            overlap: int = 200
            ) -> Iterator[MinimalSource]:
        """Abstract method to split content into chunks.

        Args:
            content (str): The raw text content of the file.
            file_path (str): The relative path of the file.
            max_size (int): The maximum character size for each chunk.

        Yields:
            Iterator[MinimalSource]: An iterator of type-safe chunk metadata.
        """

        overlap = min(overlap, max_size//2)
        lines = content.splitlines(keepends=True)

        start_index = 0
        current_chunk_length = 0

        state = self._init_state()

        def yield_and_clear_buffer() -> Iterator[MinimalSource]:
            nonlocal current_chunk_length, start_index
            if current_chunk_length > 0:
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                )
                start_index += current_chunk_length
                current_chunk_length = 0

        for line in lines:
            line_length = len(line)

            if line_length > max_size:
                yield from yield_and_clear_buffer()

                for index in range(0, line_length, max_size):
                    line_slice = line[index:index + max_size]
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index + index,
                        last_character_index=start_index + index + len(line_slice)
                    )
                start_index += line_length
                continue

            if self._should_cut(line, current_chunk_length, max_size, state):
                yield from yield_and_clear_buffer()

            if current_chunk_length + line_length > max_size:
                if current_chunk_length > 0:
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index,
                        last_character_index=start_index + current_chunk_length
                    )
                    actual_overlap = min(overlap, current_chunk_length)
                    start_index += current_chunk_length - actual_overlap
                    current_chunk_length = actual_overlap
                else:
                    yield from yield_and_clear_buffer()

            current_chunk_length += line_length

        yield from yield_and_clear_buffer()

    def _init_state(self) -> dict[str | None, bool | None]:
        state = {}
        return state

    @abstractmethod
    def should_cut(
        self,
        line: str,
        current_chunk_length: int,
        max_size: int,
        state: dict | None
    ) -> bool:
        pass


class TxtChunker(Chunker):

    def should_cut(
        self, line: str, current_chunk_length: int,
        max_size: int, state: dict | None
    ) -> bool:
        return not line.strip() and current_chunk_length > 0.5 * max_size
    # def chunk(
    #         self,
    #         content: str,
    #         file_path: str,
    #         max_size: int,
    #         overlap: int = 200
    #         ) -> Iterator[MinimalSource]:
    # """Chunking strategy optimized for .txt files."""
    # def chunk(
    #         self,
    #         content: str,
    #         file_path: str,
    #         max_size: int,
    #         overlap: int = 200
    #         ) -> Iterator[MinimalSource]:
    #     """Split .txt files by slices, if possible by logical blocks

    #     Args:
    #         content (str): The content of the .txt file.
    #         file_path (str): The relative path to the .txt file.
    #         max_size (int): The maximum character size for each chunk.

    #     Yields:
    #         Iterator[MinimalSource]: Chunks of .txt file.
    #     """
    #     overlap = min(overlap, max_size//2)
    #     lines = content.splitlines(keepends=True)

    #     start_index = 0
    #     current_chunk_length = 0

    #     def yield_and_clear_buffer() -> Iterator[MinimalSource]:
    #         nonlocal current_chunk_length, start_index
    #         if current_chunk_length > 0:
    #             yield MinimalSource(
    #                 file_path=file_path,
    #                 first_character_index=start_index,
    #                 last_character_index=start_index + current_chunk_length
    #             )
    #             start_index += current_chunk_length
    #             current_chunk_length = 0

    #     for line in lines:
    #         line_length = len(line)

    #         if line_length > max_size:
    #             yield from yield_and_clear_buffer()

    #             for index in range(0, line_length, max_size):
    #                 line_slice = line[index:index + max_size]
    #                 yield MinimalSource(
    #                     file_path=file_path,
    #                     first_character_index=start_index + index,
    #                     last_character_index=start_index + index + len(line_slice)
    #                 )
    #             start_index += line_length
    #             continue

    #         if not line.strip() and current_chunk_length > 0.5 * max_size:
    #             yield from yield_and_clear_buffer()

    #         if current_chunk_length + line_length > max_size:
    #             if current_chunk_length > 0:
    #                 yield MinimalSource(
    #                     file_path=file_path,
    #                     first_character_index=start_index,
    #                     last_character_index=start_index + current_chunk_length
    #                 )
    #                 actual_overlap = min(overlap, current_chunk_length)
    #                 start_index += current_chunk_length - actual_overlap
    #                 current_chunk_length = actual_overlap
    #             else:
    #                 yield from yield_and_clear_buffer()

    #         current_chunk_length += line_length

    #     yield from yield_and_clear_buffer()


class PyChunker(Chunker):
    def _init_state(self):
        return {"is_in_decorator_block": False}

    def should_cut(
        self, line: str, current_chunk_length: int,
        max_size: int, state: dict | None
    ) -> bool:

        stripped_line = line.lstrip()
        indentation = len(line) - len(stripped_line)
        should_cut = False
        is_boundary = stripped_line.startswith((
                "if TYPE_CHECKING:",
                "__all__", "if __name__"
            ))

        if indentation == 0:
            if stripped_line.startswith(("def ", "class ", "async def ")):
                if not state["is_in_decorator_block"]:
                    should_cut = True
                    state["is_in_decorator_block"] = False

            elif stripped_line.startswith("@"):
                if not state["is_in_decorator_block"]:
                    should_cut = True
                    state["is_in_decorator_block"] = True

            elif is_boundary:
                if not state["is_in_decorator_block"]:
                    should_cut = True
                    state["is_in_decorator_block"] = False
        return should_cut


    # """Chunking strategy optimized for Python source code."""
    # def chunk(
    #         self, content: str,
    #         file_path: str,
    #         max_size: int,
    #         overlap: int = 200
    #         ) -> Iterator[MinimalSource]:
    #     """Split Python code by classes, functions, or logical blocks.

    #     Args:
    #         content (str): The raw Python source code.
    #         file_path (str): The relative path to the .py file.
    #         max_size (int): The maximum character size for each chunk.

    #     Yields:
    #         Iterator[MinimalSource]: Chunks respecting Python syntax limits.
    #     """
    #     overlap = min(overlap, max_size//2)
    #     lines = content.splitlines(keepends=True)


    # def _should_cut(self, line: str, current_chunk_length: int, max_size: int, state: dict) -> bool:
    #     stripped_line = line.lstrip()
    #     indentation = len(line) - len(stripped_line)

    #     is_boundary = stripped_line.startswith((
    #         "if TYPE_CHECKING:", "__all__", "if __name__"
    #     ))

    #     should_cut = False

    #     if indentation == 0:
    #         if stripped_line.startswith(("def ", "class ", "async def ")):
    #             if not state["is_in_decorator_block"]:
    #                 should_cut = True
    #             state["is_in_decorator_block"] = False

    #         elif stripped_line.startswith("@"):
    #             if not state["is_in_decorator_block"]:
    #                 should_cut = True
    #             state["is_in_decorator_block"] = True

    #         elif is_boundary:
    #             if not state["is_in_decorator_block"]:
    #                 should_cut = True
    #             state["is_in_decorator_block"] = False

    #     return should_cut


    #     start_index = 0
    #     current_chunk_length = 0
    #     is_in_decorator_block = False

    #     def yield_and_clear_buffer() -> Iterator[MinimalSource]:
    #         nonlocal current_chunk_length, start_index
    #         if current_chunk_length > 0:
    #             yield MinimalSource(
    #                 file_path=file_path,
    #                 first_character_index=start_index,
    #                 last_character_index=start_index + current_chunk_length
    #             )
    #             start_index += current_chunk_length
    #             current_chunk_length = 0

    #     for line in lines:
    #         line_length = len(line)

    #         if line_length > max_size:
    #             yield from yield_and_clear_buffer()

    #             for index in range(0, line_length, max_size):
    #                 line_slice = line[index:index + max_size]
    #                 yield MinimalSource(
    #                     file_path=file_path,
    #                     first_character_index=start_index + index,
    #                     last_character_index=start_index + index + len(line_slice)
    #                 )
    #             start_index += line_length
    #             continue

            stripped_line = line.lstrip()
            indentation = line_length - len(stripped_line)

            is_boundary = stripped_line.startswith((
                "if TYPE_CHECKING:",
                "__all__", "if __name__"
            ))

            if indentation == 0:
                if stripped_line.startswith(("def ", "class ", "async def ")):
                    if not is_in_decorator_block:
                        yield from yield_and_clear_buffer()
                    is_in_decorator_block = False

                elif stripped_line.startswith("@"):
                    if not is_in_decorator_block:
                        yield from yield_and_clear_buffer()
                    is_in_decorator_block = True

                elif is_boundary:
                    if not is_in_decorator_block:
                        yield from yield_and_clear_buffer()
                    is_in_decorator_block = False

            if current_chunk_length + line_length > max_size:
                if current_chunk_length > 0:
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index,
                        last_character_index=start_index + current_chunk_length
                    )
                    actual_overlap = min(overlap, current_chunk_length)
                    start_index += current_chunk_length - actual_overlap
                    current_chunk_length = actual_overlap
                else:
                    yield from yield_and_clear_buffer()

    #         current_chunk_length += line_length

    #     yield from yield_and_clear_buffer()


class MdChunker(Chunker):
    def chunk(self, content: str, file_path: str, max_size: int):
        pass
# 1. Séparer le fichier en une liste de lignes (avec splitlines(keepends=True)).
# 2. Initialiser un buffer vide, les index (start_index = 0, current_len = 0).
# 3. Initialiser un booléen (in_code_block = False) pour tracker les blocs ```.

# 4. Pour chaque ligne du fichier :
#     a. Calculer sa longueur (line_len).
#     b. Détecter si la ligne ouvre ou ferme un bloc de code (commence par ```).
#        -> Si oui, inverser la valeur de in_code_block.

#     c. Condition de découpage "Intelligent" :
#        -> Est-ce que la ligne commence par "#" (Titre #, ##, ###) ET qu'on n'est PAS dans un bloc de code ?
#        -> Si oui ET que le buffer n'est pas vide :
#           -> On YIELD le MinimalSource accumulé jusqu'ici.
#           -> On vide le buffer (current_len = 0) et met à jour start_index.

#     d. Sécurité de taille (Garde-fou strict) :
#        -> Si (current_len + line_len) > max_size :
#           -> Si on est au milieu d'un bloc de code OU d'un paragraphe, on est obligé de couper de force.
#           -> On YIELD le MinimalSource accumulé, on vide le buffer et met à jour start_index.

#     e. Ajouter la ligne au buffer, et faire : current_len += line_len

# 5. En dehors de la boucle : YIELD le reste du buffer s'il contient encore du texte.

if __name__ == "__main__":
    import os
    from src.models import MinimalSource

    TARGET_FILE = "vllm-0.10.1/requirements/test.txt"
    MAX_SIZE_LIMIT = 2000

    print("=" * 60)
    print(f"ANALYSE ET DÉCOUPAGE DE : {TARGET_FILE}")
    print("=" * 60)

    if not os.path.exists(TARGET_FILE):
        print(f"❌ Erreur : Le fichier '{TARGET_FILE}' n'a pas été trouvé.")
    else:
        with open(TARGET_FILE, mode="r", encoding="utf-8") as f:
            real_content = f.read()

        txt_chunker = TxtChunker()
        chunks = list(txt_chunker.chunk(
            content=real_content,
            file_path=TARGET_FILE,
            max_size=MAX_SIZE_LIMIT
        ))

        # 4. Affichage des statistiques globales (Validation)
        total_chunks = len(chunks)
        print(f"📊 Statistiques d'ingestion :")
        print(f"   - Nombre total de caractères dans le fichier : {len(real_content)}")
        print(f"   - Nombre de chunks générés : {total_chunks}")
        print("-" * 60)

        # 5. Affichage d'un échantillon (ex: les 3 premiers chunks)
        for i, source in enumerate(chunks, 1):
            extracted_text = real_content[source.first_character_index : source.last_character_index]

            print(f"\n🔍 [ÉCHANTILLON] CHUNK N°{i}/{total_chunks}")
            print(f"   Index caractères : [{source.first_character_index} -> {source.last_character_index}]")
            print(f"   Taille du chunk : {len(extracted_text)} caractères")
            print("." * 40)
            # On affiche les 5 premières lignes pour inspecter le contenu visuellement
            sample_lines = extracted_text.splitlines()[:5]
            for line in sample_lines:
                # print(f"   | {line.endwith('\n') and line or line + '\n'}", end="")
                print(f"{line}")
            if len(extracted_text.splitlines()) > 5:
                print("   | [... reste du contenu masqué ...]")
            print("." * 40)

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






class PyChunker(Chunker):
    """Chunking strategy optimized for Python source code."""

    def chunk(
        self, content: str, file_path: str, max_size: int, overlap: int = 200
    ) -> Iterator[MinimalSource]:
        """Split Python code by classes, functions, or logical blocks.

        Args:
            content (str): The raw Python source code.
            file_path (str): The relative path to the .py file.
            max_size (int): The maximum character size for each chunk.

        Yields:
            Iterator[MinimalSource]: Chunks respecting Python syntax limits.
        """
        overlap = min(overlap, max_size // 2)
        lines = content.splitlines(keepends=True)

        start_index = 0
        current_chunk_length = 0
        is_in_decorator_block = False

        def yield_and_clear_buffer() -> Iterator[MinimalSource]:
            nonlocal current_chunk_length, start_index
            if current_chunk_length > 0:
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length,
                )
                start_index += current_chunk_length
                current_chunk_length = 0

        for line in lines:
            line_length = len(line)

            # 1. Gestion des lignes géantes uniques
            if line_length > max_size:
                yield from yield_and_clear_buffer()

                for index in range(0, line_length, max_size):
                    line_slice = line[index : index + max_size]
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index + index,
                        last_character_index=(
                            start_index + index + len(line_slice)
                        ),
                    )
                start_index += line_length
                continue

            stripped_line = line.strip()
            indentation = line_length - len(stripped_line)

            # Correction de syntaxe pour s'assurer de matcher les mots isolés
            is_boundary = stripped_line.startswith((
                "class ", "def ", "async def ", "if TYPE_CHECKING:",
                "__all__", "if __name__"
            ))

            # 2. Coupure propre sur frontière sémantique globale (Indentation 0)
            if indentation == 0:
                if stripped_line.startswith("@"):
                    yield from yield_and_clear_buffer()
                    is_in_decorator_block = True
                elif is_boundary:
                    if not is_in_decorator_block:
                        yield from yield_and_clear_buffer()
                    is_in_decorator_block = False
                elif stripped_line:
                    is_in_decorator_block = False

            # 3. Coupure forcée par la taille limite (Gestion de l'Overlap)
            if current_chunk_length + line_length > max_size:
                if current_chunk_length > 0:
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index,
                        last_character_index=start_index + current_chunk_length,
                    )
                    actual_overlap = min(overlap, current_chunk_length)
                    start_index += current_chunk_length - actual_overlap
                    current_chunk_length = actual_overlap
                else:
                    yield from yield_and_clear_buffer()

            # 4. Accumulation systématique de la ligne courante
            current_chunk_length += line_length

        # 5. Vidage du dernier morceau restant en fin de fichier
        yield from yield_and_clear_buffer()

def chunk(self, content: str, file_path: str, max_size: int) -> Iterator[MinimalSource]:
        """Split Python code into chunks using an indentation and structural strategy.

        Args:
            content (str): The raw Python source code.
            file_path (str): The relative path to the .py file.
            max_size (int): The maximum character size for each chunk.

        Yields:
            Iterator[MinimalSource]: Type-safe chunk metadata.
        """
        lines = content.splitlines(keepends=True)

        start_index = 0
        current_chunk_length = 0

        for line in lines:
            line_len = len(line)
            stripped_line = line.lstrip()

            # 1. Edge Case Absolu : La ligne géante qui dépasse max_size à elle seule
            if line_len > max_size:
                # Si on a déjà du contenu accumulé, on le livre d'abord
                if current_chunk_length > 0:
                    yield MinimalSource(
                        file_path=file_path,
                              first_character_index=start_index,
                        last_character_index=start_index + current_chunk_length
                    )
                    start_index += current_chunk_length
                    current_chunk_length = 0

                # Découpage forcé de cette ligne unique par tranches (slicing)
                for offset in range(0, line_len, max_size):
                    chunk_slice = line[offset : offset + max_size]
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index + offset,
                        last_character_index=start_index + offset + len(chunk_slice)
                    )

                start_index += line_len
                continue

            # 2. Détection d'une frontière logique majeure (Niveau Global / Indentation 0)
            # On calcule l'indentation : différence de taille entre la ligne brute et nettoyée
            indentation = line_len - len(stripped_line)

            is_structural_boundary = (
                stripped_line.startswith(("def ", "class ", "async def "))
                or stripped_line.startswith("#")
            )

            # Si on est à la racine (indentation 0) sur une frontière et qu'on a déjà du texte
            if indentation == 0 and is_structural_boundary and current_chunk_length > 0:
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                )
                start_index += current_chunk_length
                current_chunk_length = 0

            # 3. Sécurité de taille : Si l'accumulation dépasse la limite stricte du sujet
            if current_chunk_length + line_len > max_size:
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                )
                start_index += current_chunk_length
                current_chunk_length = 0

            # On accumule la ligne courante
            current_chunk_length += line_len

        # 4. Edge Case Final : Ne pas oublier le dernier morceau après la boucle
        if current_chunk_length > 0:
            yield MinimalSource(
                file_path=file_path,
                first_character_index=start_index,
                last_character_index=start_index + current_chunk_length
            )


def chunk(self, content: str, file_path: str, max_size: int) -> Iterator[MinimalSource]:
        """Split Markdown documentation into chunks based on headers and paragraphs.

        Args:
            content (str): The raw Markdown text.
            file_path (str): The relative path to the .md file.
            max_size (int): The maximum character size for each chunk.

        Yields:
            Iterator[MinimalSource]: Type-safe chunk metadata.
        """
        lines = content.splitlines(keepends=True)

        start_index = 0
        current_chunk_length = 0
        in_code_block = False

        for line in lines:
            line_len = len(line)
            stripped_line = line.strip()

            # 1. Edge Case Absolu : La ligne de texte ou de code géante
            if line_len > max_size:
                if current_chunk_length > 0:
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index,
                        last_character_index=start_index + current_chunk_length
                    )
                    start_index += current_chunk_length
                    current_chunk_length = 0

                for offset in range(0, line_len, max_size):
                    chunk_slice = line[offset : offset + max_size]
                    yield MinimalSource(
                        file_path=file_path,
                        first_character_index=start_index + offset,
                        last_character_index=start_index + offset + len(chunk_slice)
                    )
                start_index += line_len
                continue

            # 2. Tracking des blocs de code (```) pour ne pas couper au milieu d'un exemple
            if stripped_line.startswith("```"):
                in_code_block = not in_code_block

            # 3. Détection d'une frontière de titre Markdown (#, ##, ###, etc.)
            # On ne coupe sur un titre QUE si on se trouve en dehors d'un bloc de code
            is_header = stripped_line.startswith("#") and not in_code_block

            if is_header and current_chunk_length > 0:
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                )
                start_index += current_chunk_length
                current_chunk_length = 0

            # 4. Sécurité de débordement de taille
            if current_chunk_length + line_len > max_size:
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length
                )
                start_index += current_chunk_length
                current_chunk_length = 0

            current_chunk_length += line_len

        # 5. On vide le dernier morceau restant
        if current_chunk_length > 0:
            yield MinimalSource(
                file_path=file_path,
                first_character_index=start_index,
                last_character_index=start_index + current_chunk_length
            )

if __name__ == "__main__":
    import os
    from src.models import MinimalSource

    # 1. Spécifie le chemin vers un vrai fichier de ton dépôt vLLM
    # Exemple : un fichier central de vLLM (adapte le chemin si nécessaire)
    TARGET_FILE = "raw_corpus/vllm/engine/llm_engine.py"
    MAX_SIZE_LIMIT = 2000

    print("=" * 60)
    print(f"ANALYSE ET DÉCOUPAGE DE : {TARGET_FILE}")
    print("=" * 60)

    if not os.path.exists(TARGET_FILE):
        print(f"❌ Erreur : Le fichier '{TARGET_FILE}' n'a pas été trouvé.")
        print("Vérifie ton chemin ou remplace-le par un fichier existant dans ton dépôt.")
    else:
        # 2. Lecture du vrai contenu du fichier
        with open(TARGET_FILE, mode="r", encoding="utf-8") as f:
            real_content = f.read()

        # 3. Instanciation et exécution du découpeur
        py_chunker = PyChunker()
        chunks = list(py_chunker.chunk(
            content=real_content,
            file_path=TARGET_FILE,
            max_size=MAX_SIZE_LIMIT
        ))

        # 4. Affichage des statistiques globales (Validation)
        total_chunks = len(chunks)
        print(f"📊 Statistiques d'ingestion :")
        print(f"   - Nombre total de caractères dans le fichier : {len(real_content)}")
        print(f"   - Nombre de chunks générés : {total_chunks}")
        print("-" * 60)

        # 5. Affichage d'un échantillon (ex: les 3 premiers chunks)
        for i, source in enumerate(chunks[:3], 1):
            extracted_text = real_content[source.first_character_index : source.last_character_index]

            print(f"\n🔍 [ÉCHANTILLON] CHUNK N°{i}/{total_chunks}")
            print(f"   Index caractères : [{source.first_character_index} -> {source.last_character_index}]")
            print(f"   Taille du chunk : {len(extracted_text)} caractères")
            print("." * 40)
            # On affiche les 5 premières lignes pour inspecter le contenu visuellement
            sample_lines = extracted_text.splitlines()[:5]
            for line in sample_lines:
                print(f"   | {line.endwith('\n') and line or line + '\n'}", end="")
            if len(extracted_text.splitlines()) > 5:
                print("   | [... reste du contenu masqué ...]")
            print("." * 40)

        # 6. Vérification automatique des contraintes du sujet (Edge Cases)
        print("\n🛡️ Vérification des contraintes du sujet :")
        errors = 0
        for idx, source in enumerate(chunks):
            chunk_txt = real_content[source.first_character_index : source.last_character_index]
            if len(chunk_txt) > MAX_SIZE_LIMIT:
                print(f"   ❌ Erreur au Chunk {idx+1} : Taille de {len(chunk_txt)} dépasse {MAX_SIZE_LIMIT} !")
                errors += 1

        if errors == 0:
            print(f"   ✅ Parfait ! Tous les {total_chunks} chunks respectent la limite stricte de {MAX_SIZE_LIMIT} caractères.")
