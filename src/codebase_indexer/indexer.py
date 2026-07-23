# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 11:41:42 by stephanie       #+#    #+#               #
#  Updated: 2026/07/23 17:18:37 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #
from pathlib import Path
from typing import List
from src.codebase_indexer.ingestion import CorpusVllmCompiler
from src.codebase_indexer.chunker import MdChunker, PyChunker, TxtChunker
from src.errors import RagLoadError
from src.models import MinimalSource


class DocIndexer:
    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size

    # code de test
    # def build_and_save_index(self) -> List[MinimalSource]:
    # code def
    def build_and_save_index(self) -> int:

        input_dir = Path("data/raw")

        compiler = CorpusVllmCompiler(input_dir)
        files_to_process: List[Path] = compiler.compile_corpus()

        compiler = CorpusVllmCompiler(input_dir)
        files_to_process: List[Path] = compiler.compile_corpus()

        # TEST
        print(f"Files number : {len(files_to_process)}")
        print(f"   - Python (.py) : "
              f"{sum(1 for f in files_to_process if f.suffix == '.py')}")
        print(f"   - Markdown (.md) : "
              f"{sum(1 for f in files_to_process if f.suffix == '.md')}")
        print(f"   - Texte (.txt) : "
              f"{sum(1 for f in files_to_process if f.suffix == '.txt')}")

        py_chunker = PyChunker()
        md_chunker = MdChunker()
        txt_chunker = TxtChunker()

        all_chunks: list[MinimalSource] = []

        for file_path in files_to_process:
            with open(file_path, mode="r", encoding="utf-8") as file:
                raw_content = file.read()

                path_str = str(file_path)

                if file_path.suffix == ".py":
                    chunks_list = py_chunker.chunk(
                        raw_content, path_str, self.max_chunk_size)
                elif file_path.suffix == ".txt":
                    chunks_list = txt_chunker.chunk(
                        raw_content, path_str, self.max_chunk_size)
                else:
                    chunks_list = md_chunker.chunk(
                        raw_content, path_str, self.max_chunk_size)
                if not chunks_list:
                    continue
                all_chunks.extend(chunks_list)

        if not all_chunks:
            raise RagLoadError(f"No chunk in directory: {input_dir}")

    #     5. TOKENISATION ET PRÉPARATION DE L'INDEX (Le rôle du Tokenizer) :
    #    - Créer une liste vide pour stocker les fréquences de termes et une liste pour les chunks nettoyés.
    #    - Pour chaque chunk de notre liste globale :
    #        * Extraire le texte brut.
    #        * Le nettoyer (tout passer en minuscules, filtrer la ponctuation tout en gardant les underscores du code, supprimer les mots vides ou trop courts).
    #        * Compter combien de fois chaque mot apparaît dans ce chunk précis (le Term Frequency - TF).
    #        * Sauvegarder un résumé allégé du chunk (chemin, positions, nombre total de mots nettoyés, et son TF).

    #    - Calculer la rareté globale de chaque mot dans tout le projet (le Document Frequency - DF : dans combien de chunks différents chaque mot apparaît).
    #    - Calculer la taille moyenne de tous les chunks du projet (la fameuse moyenne 'avgdl' indispensable pour le futur calcul BM25).

    # 6. ASSEMBLAGE ET PERSISTANCE :
    #    - Regrouper dans un grand dictionnaire final :
    #        * Les statistiques globales du corpus (nombre total de chunks, longueur moyenne).
    #        * Le dictionnaire global des fréquences de documents (DF).
    #        * La liste complète de tous les chunks avec leurs TF.
    #    - Créer le dossier de destination si besoin et écrire ce dictionnaire proprement dans un fichier "index.json".

    # 7. FIN :
    #    - Renvoyer le nombre total de chunks indexés avec succès.
        return len(all_chunks)
