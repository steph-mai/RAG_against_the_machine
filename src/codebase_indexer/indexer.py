# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 11:41:42 by stephanie       #+#    #+#               #
#  Updated: 2026/07/31 15:51:27 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import json
import re
import numpy
from sentence_transformers import SentenceTransformer
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

    def build_and_save_index(self, with_embeddings: bool = False) -> None:

        input_dir = Path("data/raw")

        compiler = CorpusVllmCompiler(input_dir)
        files_to_process: List[Path] = compiler.compile_corpus()

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
                elif file_path.suffix == ".md":
                    chunks_list = md_chunker.chunk(
                        raw_content, path_str, self.max_chunk_size)
                if not chunks_list:
                    continue
                all_chunks.extend(chunks_list)

        if not all_chunks:
            raise RagLoadError(f"No chunk in directory: {input_dir}")

        tokenizer = Tokenizer()

        allterms_frequency: list[dict[str, int]] = []
        clean_chunks: list[str] = []
        all_chunks_data = []
        total_len_chunks = 0

        if with_embeddings:
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            chunks_to_embed = []

        current_open_file = ""
        full_text = ""

        class_regex = re.compile(r'^class\s+([A-Za-z0-9_]+)', re.MULTILINE)
        def_regex = re.compile(r'^[ \t]*def\s+([A-Za-z0-9_]+)', re.MULTILINE)
        header_regex = re.compile(r'^(#+\s+.*)', re.MULTILINE)

        for chunk in tqdm(all_chunks, desc="Tokenizing", unit="chunk"):
            file_path = chunk.file_path
            start_index = chunk.first_character_index
            end_index = chunk.last_character_index

            if file_path != current_open_file:
                with open(file_path, mode="r", encoding="utf-8") as f:
                    full_text = f.read()
                current_open_file = file_path
                path_obj = Path(file_path)
                current_name = path_obj.name
                current_suffix = path_obj.suffix

            chunk_raw_text = full_text[start_index:end_index]

            if current_suffix == ".py":
                classes = class_regex.findall(
                    full_text[:start_index])
                class_name = classes[-1] if classes else ""

                defs = def_regex.findall(
                    full_text[:start_index])
                def_name = defs[-1] if defs else ""

                text_to_tokenize = (
                    f"{current_name} "
                    f"{class_name} {def_name} {chunk_raw_text}"
                )
            elif current_suffix == ".md":
                headers = header_regex.findall(
                    full_text[:start_index])

                last_header = headers[-1] if headers else ""

                text_to_tokenize = (
                    f"{current_name} "
                    f"{last_header} {chunk_raw_text}"
                )

            else:
                text_to_tokenize = chunk_raw_text

            chunk_clean_text = tokenizer.tokenize(
                text_to_tokenize)

            if with_embeddings:
                chunk_to_embed = text_to_tokenize
                chunks_to_embed.append(chunk_to_embed)

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

        if with_embeddings:
            batch_size = 32
            all_embeddings = []

            # On boucle par "pas" de 32 (la taille du batch)
            for i in tqdm(range(0, len(chunks_to_embed), batch_size), desc="Vectorization", unit="batch"):
                # On extrait un sous-tableau de 32 textes
                batch = chunks_to_embed[i: i + batch_size]

                # On encode uniquement ce lot
                batch_embeddings = (
                    embedder.encode(batch, show_progress_bar=False)
                )
                all_embeddings.extend(batch_embeddings)

            # On convertit le tout en une seule grande matrice NumPy
            embeddings_matrix = numpy.array(all_embeddings)
            numpy.save("data/embeddings.npy", embeddings_matrix)

        document_frequency = tokenizer.get_document_frequency(
            allterms_frequency)

        avg_len_chunks = total_len_chunks / len(all_chunks)

        general_chunks_dict = {}

        general_chunks_dict["chunks_number"] = len(all_chunks)
        general_chunks_dict["avg_len_chunks"] = avg_len_chunks
        general_chunks_dict["max_chunk_size"] = self.max_chunk_size
        general_chunks_dict["document_frequency"] = document_frequency
        general_chunks_dict["all_chunks_data"] = all_chunks_data

        output_path = Path("data/processed/index.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(general_chunks_dict, f, ensure_ascii=False, indent=4)

        if with_embeddings:
            print(
                "Bonus semantic embeddings: "
                "Vector index generated successfully!")
        else:
            print(f"Ingestion complete! "
                  f"Indices saved under {output_path.parent}/")
