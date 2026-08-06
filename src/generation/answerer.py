from typing import Any
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.core.models import MinimalAnswer, MinimalSource
import torch


class Answerer:
    def __init__(self, model_id: str = "Qwen/Qwen3-0.6B"):
        self.llm = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            dtype=torch.float32
        )
        self.model.to("cpu")

    def _format_context(self, retrieved_chunks: list[dict[str, Any]]) -> str:
        all_context = []

        for i, chunk in enumerate(retrieved_chunks):
            file_path = chunk["file_path"]
            content = chunk["content"]

            part_of_context = f"source {i + 1}: {file_path}\n{content}"
            all_context.append(part_of_context)

        return "\n\n".join(all_context)

    def generate_answer(
            self,
            question_id: str,
            query: str,
            retrieved_chunks: list[dict[str, Any]]
            ) -> MinimalAnswer:

        context = self._format_context(retrieved_chunks)

        prompt = (
            "You are a helpful technical assistant. "
            "Answer the user's question "
            "accurately and concisely using *only* "
            "the provided context below. "
            "Do not hallucinate.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )

        inputs = self.tokenizer(
            prompt, return_tensors="pt"
            ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=500,
                pad_token_id=self.tokenizer.eos_token_id
            )

        input_len = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_len:]

        response = self.tokenizer.decode(
            generated_tokens, skip_special_tokens=True).strip()

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
