# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  answerer.py                                       :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/08/10 14:01:41 by stmaire         #+#    #+#               #
#  Updated: 2026/08/11 10:29:01 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

from typing import Any
from pathlib import Path
import tqdm
import ollama
import json
import requests
import subprocess
import time
from src.core.models import (
    MinimalAnswer, MinimalSource,
    StudentSearchResultsAndAnswer
)


class Answerer:
    """Generate answers from retrieved document chunks using Ollama.

    This class checks the local Ollama server, extracts text snippets
    from disk,
    builds a prompt with the relevant context, and returns a structured answer.
    """

    def __init__(self, model_id: str = "qwen3:0.6b"):
        """Initialize the answerer.

        Args:
            model_id: Identifier of the Ollama model to use for generation.
        """
        self.model_id = model_id
        self.client = ollama.Client(host='http://127.0.0.1:11434')
        self._check_connection()

    def _check_connection(self) -> None:
        """Ensure that the local Ollama server is available.

        Raises:
            RuntimeError: If the server cannot be started automatically.
        """
        try:
            requests.get("http://127.0.0.1:11434", timeout=2)
        except requests.exceptions.ConnectionError:
            print("Ollama is starting...")

            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3)

            try:
                requests.get("http://127.0.0.1:11434", timeout=2)
            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "The Ollama server could not be started automatically. "
                    "Make sure it is installed and try running"
                    "`ollama serve` manually."
                )

    def _get_text_from_disk(
            self, file_path: str, start: int, end: int) -> str:
        """Return the text slice corresponding to a chunk in a file.

        Args:
            file_path: Path to the source file on disk.
            start: Start index of the requested slice.
            end: End index of the requested slice.

        Returns:
            The extracted text fragment, or an empty string if the file cannot
            be read or does not exist.
        """
        path = Path(file_path)
        if not path.is_file():
            return ""

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                return content[start:end]
        except Exception:
            return ""

    def _format_context(self, retrieved_chunks: list[dict[str, Any]]) -> str:
        """Build a compact context string from retrieved chunks.

        Args:
            retrieved_chunks: List of chunk dictionaries with file metadata and
                character offsets.

        Returns:
            A concatenated context string limited to a maximum length.
        """
        all_context = []
        max_context_length = 4000

        for chunk in retrieved_chunks:
            text = self._get_text_from_disk(
                chunk["file_path"],
                chunk["first_character_index"],
                chunk["last_character_index"]
            )
            if text:
                all_context.append(text)

        full_context = "\n\n---\n\n".join(all_context)

        return full_context[:max_context_length]

    def generate_answer(
        self,
        question_id: str,
        query: str,
        retrieved_chunks: list[dict[str, Any]]
    ) -> MinimalAnswer:
        """Generate an answer for one question using the retrieved context.

        Args:
            question_id: Identifier of the question being answered.
            query: User question to answer.
            retrieved_chunks: Retrieved source chunks associated with
            the query.

        Returns:
            A ``MinimalAnswer`` instance containing the answer and the sources
            used as context.

        Raises:
            RuntimeError: If the model call fails at generation time.
        """
        if not retrieved_chunks:
            return MinimalAnswer(
                question_id=question_id,
                question=query,
                retrieved_sources=[],
                answer="Information not found in context."
            )

        context = self._format_context(retrieved_chunks[:6])

        system_instruction = (
            "You are a helpful technical assistant. "
            "Answer the user's question clearly, concisely, "
            "and in natural language. "
            "You MUST base your answer EXCLUSIVELY on the content"
            "inside <context> tags. "
            "Do not invent, hallucinate, or add any external information. "
            "Do not repeat or quote the <context> or <question> tags"
            "in your answer. "
            "Write only the final answer, with no extra tags or labels."
        )

        user_content = (
            f"<context>\n{context}\n</context>\n\n"
            f"<question>\n{query}\n</question>"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ]

        try:
            response_obj = self.client.chat(
                model=self.model_id,
                messages=messages,
                think=False,
                keep_alive="10m",
                options={
                    "temperature": 0.0,
                    "num_predict": 300,
                    "repeat_penalty": 1.3,
                    "repeat_last_n": 64,
                }
            )
            response = response_obj["message"]["content"].strip()

        except Exception as e:
            raise RuntimeError(
                f"Ollama generation failed: {e}. "
                f"Make sure the model is pulled "
                f"(`ollama pull {self.model_id}`)."
            )

        retrieved_sources = [
            MinimalSource(
                file_path=chunk["file_path"],
                first_character_index=chunk["first_character_index"],
                last_character_index=chunk["last_character_index"]
            )
            for chunk in retrieved_chunks
        ]

        return MinimalAnswer(
            question_id=question_id,
            question=query,
            retrieved_sources=retrieved_sources,
            answer=response
        )

    def run(
            self, student_search_results_path: str, save_directory: str
            ) -> Path:
        """Process search results and save generated answers to disk.

        Args:
            student_search_results_path: Path to the JSON file
            containing search results.
            save_directory: Directory where the generated answer file will be
                saved.

        Returns:
            Path to the generated output JSON file.

        Raises:
            FileNotFoundError: If the input search results file does not exist.
        """
        path = Path(student_search_results_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"The search results file '{path}' does not exist. "
                "You must run `search_dataset` first."
            )

        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        queries = data["search_results"]
        k = data["k"]
        total = len(queries)

        print(f"Loaded {total} questions ...", flush=True)

        answers_list = []

        for item in tqdm.tqdm(queries, desc="Processing questions", unit="q"):
            question_id = item["question_id"]
            query = item["question"]
            retrieved_chunks = item["retrieved_sources"]

            minimal_answer = self.generate_answer(
                question_id=question_id,
                query=query,
                retrieved_chunks=retrieved_chunks
            )

            answers_list.append(minimal_answer)

        print(f"Processed {total} of {total} questions", flush=True)

        final_output = StudentSearchResultsAndAnswer(
            search_results=answers_list,
            k=k
        )

        output_dir = Path(save_directory)
        dataset_name = path.parent.name
        if dataset_name and dataset_name not in output_dir.parts:
            output_dir = output_dir / dataset_name
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / path.name

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output.model_dump_json(indent=4, exclude_none=True))

        return output_file
