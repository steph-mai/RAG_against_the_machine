"""Indexing pipeline for chunks into processed metadata and embeddings."""

import json
import re
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

from src.codebase_indexer.chunker import MdChunker, PyChunker, TxtChunker
from src.codebase_indexer.ingestion import CorpusVllmCompiler
from src.tokenizer import Tokenizer
from src.errors import RagLoadError
from src.models import MinimalSource

CLASS_REGEX = re.compile(r"^class\s+([A-Za-z0-9_]+)", re.MULTILINE)
DEF_REGEX = re.compile(r"^[ \t]*def\s+([A-Za-z0-9_]+)", re.MULTILINE)
HEADER_REGEX = re.compile(r"^(#+\s+.*)", re.MULTILINE)


class DocIndexer:
    """Build and persist an index for source-code chunks."""

    def __init__(self, max_chunk_size: int = 2000):
        """Initialize the document indexer.

        Args:
            max_chunk_size: Maximum number of characters allowed per chunk.
        """
        self.max_chunk_size = max_chunk_size
        self.input_dir = Path("data/raw")
        self.current_open_file = ""
        self.full_text = ""

    def _get_all_chunks(
        self,
        files_to_process: list[Path],
    ) -> list[MinimalSource]:
        """Chunk all selected files into reusable source metadata entries.

        Args:
            files_to_process: List of files discovered by the corpus compiler.

        Returns:
            A flat list of chunk metadata objects.

        Raises:
            RagLoadError: If no chunks are produced from the input directory.
        """
        all_chunks: list[MinimalSource] = []

        py_chunker = PyChunker()
        md_chunker = MdChunker()
        txt_chunker = TxtChunker()

        for file_path in tqdm(files_to_process, desc="Chunking", unit="file"):
            with open(file_path, mode="r", encoding="utf-8") as file:
                raw_content = file.read()

                path_str = str(file_path)

                if file_path.suffix == ".py":
                    chunks_list = py_chunker.chunk(
                        raw_content,
                        path_str,
                        self.max_chunk_size,
                    )
                elif file_path.suffix == ".txt":
                    chunks_list = txt_chunker.chunk(
                        raw_content,
                        path_str,
                        self.max_chunk_size,
                    )
                elif file_path.suffix == ".md":
                    chunks_list = md_chunker.chunk(
                        raw_content,
                        path_str,
                        self.max_chunk_size,
                    )
                else:
                    continue

                if not chunks_list:
                    continue

                all_chunks.extend(chunks_list)

        if not all_chunks:
            raise RagLoadError(f"No chunk in directory: {self.input_dir}")

        return all_chunks

    def _get_text_to_tokenize(self, chunk: MinimalSource) -> str:
        """Build the text representation used for tokenization.

        Args:
            chunk: A chunk metadata object describing a file segment.

        Returns:
            The enriched text to be tokenized for indexing.
        """
        file_path = chunk.file_path
        start_index = chunk.first_character_index
        end_index = chunk.last_character_index

        if file_path != self.current_open_file:
            with open(file_path, mode="r", encoding="utf-8") as f:
                self.full_text = f.read()
            self.current_open_file = file_path

        path_obj = Path(file_path)
        current_name = path_obj.name
        current_suffix = path_obj.suffix

        chunk_raw_text = self.full_text[start_index:end_index]

        if current_suffix == ".py":
            classes = CLASS_REGEX.findall(self.full_text[:start_index])
            class_name = classes[-1] if classes else ""

            defs = DEF_REGEX.findall(self.full_text[:start_index])
            def_name = defs[-1] if defs else ""

            text_to_tokenize = (
                f"{current_name} "
                f"{class_name} {def_name} {chunk_raw_text}"
            )
        elif current_suffix == ".md":
            headers = HEADER_REGEX.findall(self.full_text[:start_index])
            last_header = headers[-1] if headers else ""

            text_to_tokenize = (
                f"{current_name} "
                f"{last_header} {chunk_raw_text}"
            )
        else:
            text_to_tokenize = chunk_raw_text

        return text_to_tokenize

    def _get_chromaDB_collection(self, chunks_to_embed: list[str]) -> None:
        """Create and populate a ChromaDB collection with semantic embeddings.

        Args:
            chunks_to_embed: Text chunks to embed and store in ChromaDB.
        """
        chroma_client = chromadb.PersistentClient(path="data/chroma")

        try:
            chroma_client.delete_collection(name="codebase_chunks")
        except Exception:
            pass

        sentence_transformer_ef = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

        collection = chroma_client.create_collection(
            name="codebase_chunks",
            embedding_function=sentence_transformer_ef,
        )

        batch_size = 100
        for i in tqdm(
            range(0, len(chunks_to_embed), batch_size),
            desc="ChromaDB Indexing",
            unit="batch",
        ):
            batch_texts = chunks_to_embed[i: i + batch_size]
            batch_ids = [str(j) for j in range(i, i + len(batch_texts))]

            collection.add(
                documents=batch_texts,
                ids=batch_ids,
            )

        print(
            "Bonus semantic embeddings: "
            "Vector index generated successfully with ChromaDB!")

    def build_and_save_index(self, with_embeddings: bool = False) -> None:
        """Build the processed index and persist it to disk.

        Args:
            with_embeddings: Whether to also create and populate the ChromaDB
                vector collection.

        Returns:
            None
        """
        compiler = CorpusVllmCompiler(self.input_dir)
        files_to_process: List[Path] = compiler.compile_corpus()

        all_chunks = self._get_all_chunks(files_to_process)

        tokenizer = Tokenizer()

        allterms_frequency: list[dict[str, int]] = []
        clean_chunks: list[str] = []
        all_chunks_data = []
        total_len_chunks = 0

        if with_embeddings:
            chunks_to_embed = []

        self.current_open_file = ""
        self.full_text = ""

        for chunk in tqdm(all_chunks, desc="Tokenizing", unit="chunk"):
            text_to_tokenize = self._get_text_to_tokenize(chunk)

            chunk_clean_text = tokenizer.tokenize(text_to_tokenize)

            if with_embeddings:
                chunks_to_embed.append(text_to_tokenize)

            clean_chunks.append(chunk_clean_text)

            tf_in_one_chunk: dict[str, int] = (
                tokenizer.get_terms_frequency_in_one_chunk(chunk_clean_text)
            )

            allterms_frequency.append(tf_in_one_chunk)

            clean_tokens_count = len(chunk_clean_text)
            total_len_chunks += clean_tokens_count

            chunk_data: dict[str, str | int | dict[str, int]] = {
                "file_path": chunk.file_path,
                "first_character_index": chunk.first_character_index,
                "last_character_index": chunk.last_character_index,
                "clean_tokens_number": len(chunk_clean_text),
                "term_frequency": tf_in_one_chunk,
            }

            all_chunks_data.append(chunk_data)

        if with_embeddings:
            self._get_chromaDB_collection(chunks_to_embed)

        document_frequency = tokenizer.get_document_frequency(
            allterms_frequency)

        avg_len_chunks = total_len_chunks / len(all_chunks)

        general_chunks_dict = {
            "chunks_number": len(all_chunks),
            "avg_len_chunks": avg_len_chunks,
            "max_chunk_size": self.max_chunk_size,
            "document_frequency": document_frequency,
            "all_chunks_data": all_chunks_data,
        }

        output_path = Path("data/processed/index.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(general_chunks_dict, f, ensure_ascii=False, indent=4)

        if not with_embeddings:
            print(
                f"Ingestion complete! "
                f"Indices saved under {output_path.parent}/"
            )
