# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  tokenizer.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+          #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 16:41:18 by stephanie       #+#    #+#               #
#  Updated: 2026/07/24 10:03:16 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import re
from typing import List
from collections import Counter


class Tokenizer():
    """Tokenizer for raw text into cleaned terms and frequency maps."""

    def __init__(self):
        """Initialize the tokenizer with a set of stop words."""
        self.stop_words = {
            "how", "what", "why", "when", "where", "who", "whom", "which", "whose",

            "is", "are", "am", "was", "were", "be", "been", "being",
            "do", "does", "did", "have", "has", "had", "having",
            "can", "could", "will", "would", "shall", "should", "may", "might", "must",

            "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
            "you", "your", "yours", "yourself", "yourselves",
            "he", "him", "his", "himself", "she", "her", "hers", "herself",
            "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
            "this", "that", "these", "those",

            "a", "an", "the", "and", "but", "or", "if", "because", "as", "until", "while",

            "of", "at", "by", "for", "with", "about", "against", "between",
            "into", "through", "during", "before", "after", "above", "below",
            "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",

            "again", "further", "then", "once", "here", "there", "all", "any",
            "both", "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just", "now"
        }

    # def normalize_and_clean_raw_text(self, raw_text: str) -> List[str]:
    #     """Normalize and clean raw text into tokens.

    #     Text is converted to lower case, non-alphanumeric characters
    #     are replaced with spaces, and stop words and short tokens
    #     are removed.

    #     Args:
    #         raw_text: The raw text to normalize.

    #     Returns:
    #         A list of cleaned tokens.
    #     """
    #     if not raw_text:
    #         return []
    #     clean_tokens = []

    #     lower_text = raw_text.lower()
    #     cleaned_text = re.sub(r'[^a-z0-9_]', ' ', lower_text)
    #     tokens = cleaned_text.split()

    #     for token in tokens:
    #         if token in self.stop_words:
    #             continue
    #         if len(token) <= 2:
    #             continue
    #         else:
    #             clean_tokens.append(token)
    #     return clean_tokens

    def normalize_and_clean_raw_text(self, raw_text: str) -> List[str]:
        """Normalize and clean raw text into tokens (Code-Aware)."""
        if not raw_text:
            return []

        # 1. Traitement du CamelCase (ex: "AsyncLLMEngine" -> "Async LLMEngine")
        # Coupe entre une minuscule et une majuscule
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_text)

        # Coupe entre une suite de majuscules et le reste (ex: "HTTPResponse" -> "HTTP Response")
        text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)

        # 2. Remplacer TOUT ce qui n'est pas alphanumérique par un espace
        # Cela casse automatiquement le snake_case: "get_model_config" -> "get model config"
        cleaned_text = re.sub(r'[^a-zA-Z0-9]', ' ', text)

        # 3. Passage en minuscules
        lower_text = cleaned_text.lower()

        # 4. Découpage et filtrage (inchangé)
        tokens = lower_text.split()
        clean_tokens = []

        for token in tokens:
            if token in self.stop_words:
                continue
            if len(token) <= 2:  # On garde les mots de plus de 2 lettres
                continue
            else:
                clean_tokens.append(token)

        return clean_tokens

    def get_terms_frequency_in_one_chunk(
            self, clean_tokens: List[str]) -> dict[str, int]:
        """Compute term frequency for a single token list.

        Args:
            clean_tokens: A list of cleaned tokens.

        Returns:
            A dictionary mapping tokens to their frequency counts.
        """
        terms_frequency_dict = Counter(clean_tokens)
        return terms_frequency_dict

    def get_document_frequency(
            self, all_term_frequencies: list[dict[str, int]]
            ) -> dict[str, int]:
        """Compute document frequency across multiple term frequency maps.

        Args:
            all_term_frequencies: A list of term frequency dictionaries,
                one per document or chunk.

        Returns:
            A dictionary mapping each token to the number of documents
            in which it appears.
        """
        doc_frequency_dict = Counter()
        for terms_frequency_dict in all_term_frequencies:
            for word in terms_frequency_dict.keys():
                doc_frequency_dict[word] += 1
        return doc_frequency_dict


if __name__ == "__main__":
    raw_text = "ctr counts are {3:4, 2:3, 1:1} ctr.most_common(2) picks: \
        3 with count 4 and 2 with count 3"
    tokenizer = Tokenizer()
    clean_tokens = tokenizer.normalize_and_clean_raw_text(raw_text)
    print(clean_tokens)
    terms_frequency_dict = tokenizer.get_terms_frequency_in_one_chunk(
        clean_tokens)
    print(terms_frequency_dict)
