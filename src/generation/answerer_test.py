from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class Answerer:
    """Handles natural language answer generation using Qwen/Qwen3-0.6B."""

    def __init__(self, model_name: str = "Qwen/Qwen3-0.6B"):
        """Initialize the tokenizer and the Qwen/Qwen3-0.6B model."""
        self.model_name = model_name
        print(f"Loading model {model_name}...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

    def _format_context(self, retrieved_chunks: list[dict]) -> str:
        """Format retrieved chunks into a clean context block."""
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks):
            file_path = chunk.get("file_path", "unknown")
            content = chunk.get("content", "")
            context_parts.append(f"Source [{i+1}] ({file_path}):\n{content}")

        return "\n\n".join(context_parts)

    def answer(self, query: str, chunks: list[dict], max_new_tokens: int = 512) -> str:
        """Generate a grounded answer based on the query and retrieved chunks.

        Args:
            query: The user question.
            chunks: List of retrieved chunk dictionaries.
            max_new_tokens: Maximum tokens to generate.

        Returns:
            The generated answer text.
        """
        context = self._format_context(chunks)

        # Utilisation d'un prompt structuré adapté aux consignes du sujet
        prompt = (
            "You are a helpful technical assistant. Answer the user's question "
            "accurately and concisely using *only* the provided context below. "
            "Do not hallucinate.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.1,  # Faible pour rester fidèle au contexte
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        input_len = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_len:]
        answer_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return answer_text.strip()
