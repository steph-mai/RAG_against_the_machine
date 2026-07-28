# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 11:41:42 by stephanie       #+#    #+#               #
#  Updated: 2026/07/28 17:26:58 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import json
from tqdm import tqdm
from pathlib import Path
from typing import List
from src.codebase_indexer.ingestion import CorpusVllmCompiler
from src.codebase_indexer.chunker import MdChunker, PyChunker, TxtChunker
from src.tokenizer import Tokenizer
from src.errors import RagLoadError
from src.models import MinimalSource


class DocIndexer:
    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size

    # code de test
    # def build_and_save_index(self) -> List[MinimalSource]
    # code def
    def build_and_save_index(self) -> None:

        input_dir = Path("data/raw")

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

        for file_path in tqdm(files_to_process, desc="Chunking", unit="file"):
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

        tokenizer = Tokenizer()

        #    - Créer une liste vide pour stocker les fréquences de termes et
        # une liste pour les chunks nettoyés.
        allterms_frequency: list[dict[str, int]] = []
        clean_chunks: list[str] = []
        all_chunks_data = []
        total_len_chunks = 0

        for chunk in tqdm(all_chunks, desc="Tokenizing", unit="chunk"):
            file_path = chunk.file_path
            start_index = chunk.first_character_index
            end_index = chunk.last_character_index

            with open(file_path, mode="r", encoding="utf-8") as f:
                f.seek(start_index)
                chunk_raw_text = f.read(end_index - start_index)

                file_name = Path(file_path).name
                text_to_tokenize = f"{file_name} {chunk_raw_text}"

                chunk_clean_text = tokenizer.normalize_and_clean_raw_text(text_to_tokenize)

                clean_chunks.append(chunk_clean_text)

                tf_in_one_chunk: dict[str, int] = (
                    tokenizer.get_terms_frequency_in_one_chunk(
                        chunk_clean_text))

                allterms_frequency.append(tf_in_one_chunk)

                clean_tokens_count = len(chunk_clean_text)
                total_len_chunks += clean_tokens_count

                chunk_data: dict[str, str | int | dict[str, int]] = {}
                chunk_data["file_path"] = chunk.file_path
                chunk_data["first_character_index"] = start_index
                chunk_data["last_character_index"] = end_index
                chunk_data["clean_tokens_number"] = len(chunk_clean_text)
                chunk_data["term_frequency"] = tf_in_one_chunk

            all_chunks_data.append(chunk_data)

        document_frequency = tokenizer.get_document_frequency(
            allterms_frequency)
        # Calculer la rareté globale de chaque mot dans tout le projet
        # (le Document Frequency - DF : dans combien de chunks différents
        # chaque mot apparaît).

        avg_len_chunks = total_len_chunks / len(all_chunks)
        #    - Calculer la taille moyenne de tous les chunks du projet
        # (la moyenne 'avgdl' indispensable pour le futur calcul BM25).

    # 6. ASSEMBLAGE ET PERSISTANCE :
        general_chunks_dict = {}

        general_chunks_dict["chunks_number"] = len(all_chunks)
        general_chunks_dict["avg_len_chunks"] = avg_len_chunks
        general_chunks_dict["document_frequency"] = document_frequency
        general_chunks_dict["all_chunks_data"] = all_chunks_data

        output_path = Path("data/processed/index.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(general_chunks_dict, f, ensure_ascii=False, indent=4)

        print(f"Ingestion complete! "
              f"Indexed {len(all_chunks)} chunks under data/processed/")

        return output_path
