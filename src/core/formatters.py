from src.core.models import MinimalAnswer


class Formatter:
    """Format and display RAG pipeline results for CLI output."""

    def print_answer(self, result: MinimalAnswer) -> None:
        """Print a formatted answer with its sources.

        Args:
            result: The generated answer with retrieved sources.

        Returns:
            None
        """
        print(f"\n{'='*60}")
        print(f"QUESTION: {result.question}")
        print(f"{'='*60}\n")
        print(f"ANSWER:\n{result.answer}\n")
        self._print_sources(result)

    def _print_sources(self, result: MinimalAnswer) -> None:
        """Print the list of retrieved sources for an answer.

        Args:
            result: The generated answer with retrieved sources.

        Returns:
            None
        """
        print(f"{'-'*60}")
        print(f"SOURCES ({len(result.retrieved_sources)}):")
        for i, src in enumerate(result.retrieved_sources, 1):
            print(
                f"  [{i}] {src.file_path}  "
                f"(chars {src.first_character_index}-"
                f"{src.last_character_index})"
            )
        print(f"{'='*60}\n")
