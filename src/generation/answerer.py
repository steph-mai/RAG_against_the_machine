from typing import Any
from pathlib import Path
import tqdm
import ollama
import json
import requests
from src.core.models import (
    MinimalAnswer, MinimalSource,
    StudentSearchResultsAndAnswer,
    ChunkContent
)


class Answerer:
    def __init__(self, model_id: str = "qwen3:0.6b"):
        self.model_id = model_id
        self.client = ollama.Client(host='http://127.0.0.1:11434')
        self._check_connection()

    def _check_connection(self) -> None:
        try:
            requests.get("http://127.0.0.1:11434", timeout=5)
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "The Ollama server could not be found. "
                "Make sure it is running (command: `ollama serve`) "
                "in another terminal window and try again."
            )

    def _format_context(self, retrieved_chunks: list[dict[str, Any]]) -> str:
        all_context = []

        for chunk in retrieved_chunks:
            chunk_obj = ChunkContent(
                file_path=chunk["file_path"],
                first_character_index=chunk["first_character_index"],
                last_character_index=chunk["last_character_index"],
                text=chunk.get("content", "")
            )

            all_context.append(chunk_obj.text)

        return "\n\n---\n\n".join(all_context)

    def generate_answer(
            self,
            question_id: str,
            query: str,
            retrieved_chunks: list[dict[str, Any]]
            ) -> MinimalAnswer:

        context = self._format_context(retrieved_chunks[:6])

        system_instruction = (
            "You are an expert technical assistant. "
            "Extract the exact bash commands and technical steps strictly from the provided context to answer the user's question. "
            "Provide ONLY the direct instructions. Do not use introductory filler, conversational text, or mention the source material. "
            "If the exact steps cannot be found in the context, reply exactly with: "
            "\"Information not found in context.\""
        )

        user_content = (
            f"Context:\n{context}\n\n"
            f"Question: {query}"
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
                options={
                    "temperature": 0.3,
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
                "(`ollama pull {self.model_id}`)."
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
            answer=response,
            retrieved_contents=[
                chunk.get("content", "") for chunk in retrieved_chunks]
        )

    def run(
            self, student_search_results_path: str, save_directory: str
            ) -> Path:
        """Process a dataset of search results and save generated answers."""
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
            contents = item.get("retrieved_contents", [])

            # Injection du texte pour l'Answerer
            retrieved_chunks_with_content = [
                {**source, "content": content}
                for source, content in zip(retrieved_chunks, contents)
            ]

            minimal_answer = self.generate_answer(
                question_id=question_id,
                query=query,
                retrieved_chunks=retrieved_chunks_with_content
            )

            # (Optionnel) Si 'retrieved_contents' est
            # de trop dans la réponse finale
            # minimal_answer.retrieved_contents = []

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

        # exclude={"search_results": {"__all__": {"retrieved_contents"}}}
        # supprime l'affichage du content dans l'output final si besoin !
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output.model_dump_json(indent=4, exclude_none=True))

        return output_file
