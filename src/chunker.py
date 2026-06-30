# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  chunker.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/30 15:28:09 by stephanie       #+#    #+#               #
#  Updated: 2026/06/30 18:02:39 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #
"""Module defining the chunking strategies for different file types."""
from abc import abstractmethod, ABC
from src.models import MinimalSource
from typing import Iterator


class Chunker(ABC):
    """Abstract base class for document chunking strategies."""
    @abstractmethod
    def chunk(self, content: str, file_path: str, max_size: int):
        """Abstract method to split content into chunks.

        Args:
            content (str): The raw text content of the file.
            file_path (str): The relative path of the file.
            max_size (int): The maximum character size for each chunk.

        Yields:
            Iterator[MinimalSource]: An iterator of type-safe chunk metadata.
        """
        pass

    def is_inferior_to_max_size(self, chunk: str, max_size: int):
        """Check if a chunk's length is within the allowed limit.

        Args:
            chunk_content (str): The text content of the chunk.
            max_size (int): The maximum allowed size.

        Returns:
            bool: True if the chunk is within limits, False otherwise.
        """
        return len(chunk) <= max_size


class PyChunker(Chunker):
    """Chunking strategy optimized for Python source code."""
    def chunk(self, content: str, file_path: str, max_size: int) -> Iterator[MinimalSource]:
        """Split Python code by classes, functions, or logical blocks.

        Args:
            content (str): The raw Python source code.
            file_path (str): The relative path to the .py file.
            max_size (int): The maximum character size for each chunk.

        Yields:
            Iterator[MinimalSource]: Chunks respecting Python syntax limits.
        """

        # 1. Séparer le fichier en une liste de lignes (avec splitlines(keepends=True)).
        # 2. Initialiser un buffer vide et les index (start_index = 0, current_len = 0).

        # 3. Pour chaque ligne du fichier :
        #     a. Calculer sa longueur (line_len).
        #     b. Vérifier si la ligne est une "Frontière Majeure" :
        #     -> Est-ce qu'elle matche la Regex (def, class, #) ET a une indentation de 0 ?

        #     c. Si c'est une Frontière Majeure ET que ton buffer n'est pas vide :
        #     -> On regarde si le buffer actuel est assez grand pour faire un chunk pertinent.
        #     -> Si oui : on YIELD le MinimalSource actuel, on met à jour start_index, et on vide le buffer.

        #     d. Cas limite (Garde-fou strict du sujet) :
        #     -> Si (current_len + line_len) > max_size (2000) :
        #         -> On n'a plus le choix, on doit couper immédiatement pour respecter la limite.
        #         -> On YIELD le MinimalSource, on met à jour start_index, et on vide le buffer.

        #     e. Ajouter la ligne au buffer, et faire : current_len += line_len

        # 4. En dehors de la boucle : YIELD le reste du buffer s'il contient encore du code.

        lines = content.splitlines(keepends=True)

        start_index = 0
        current_chunk_length = 0

        for line in lines:
            line_length = len(line)

            if line_length > max_size:
                pass
            if current_chunk_length + line_length > max_size:
                end_index = start_index + current_chunk_length
                yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=end_index)
            start_index = end_index
            current_chunk_length = 0
        if current_chunk_length > 0:
            yield MinimalSource(
                    file_path=file_path,
                    first_character_index=start_index,
                    last_character_index=start_index + current_chunk_length)




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




