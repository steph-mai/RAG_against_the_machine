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
