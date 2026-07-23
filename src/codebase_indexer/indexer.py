# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  indexer.py                                        :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 11:41:42 by stephanie       #+#    #+#               #
#  Updated: 2026/07/23 16:23:37 by stephanie       ###   ########.fr        #
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

        # 6. TODO: Passer all_chunks au Tokenizer pour TF-IDF / BM25
        # final_index = self.tokenizer.build_vocabulary_and_tokenize(all_chunks)
        # 7. TODO: Sauvegarder dans data/processed/index.json
        # self._save_to_json(final_index, Path("data/processed/index.json"))

        # code de test
        # return all_chunks
        # code def
        return len(all_chunks)
