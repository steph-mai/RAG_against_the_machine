# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  tokenizer.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/08/04 16:04:34 by stmaire         #+#    #+#               #
#  Updated: 2026/08/04 16:04:40 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import re
from typing import List
from collections import Counter

STOP_WORDS = {
    "how", "what", "why", "when", "where", "who", "whom", "which",
    "whose",

    "is", "are", "am", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had", "having", "can",
    "could", "will", "would", "shall", "should", "may",
    "might", "must",

    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "this", "that", "these", "those",

    "a", "an", "the", "and", "but", "or", "if", "because", "as",
    "until", "while",

    "of", "at", "by", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below",
    "to", "from", "up", "down", "in", "out", "on", "off", "over",
    "under",

    "again", "further", "then", "once", "here", "there", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "just", "now"
}

CAMEL_CASE_LOWER_TO_UPPER = re.compile(r'([a-z])([A-Z])')
CAMEL_CASE_ACRONYM_TO_WORD = re.compile(r'([A-Z])([A-Z][a-z])')
NON_ALPHANUMERIC = re.compile(r'[^a-zA-Z0-9]')


class Tokenizer:
    """Tokenizer for raw text into cleaned terms and frequency maps."""

    def __init__(self) -> None:
        """Initialize the tokenizer with a set of stop words."""
        self.stop_words = STOP_WORDS

    def tokenize(self, raw_text: str) -> List[str]:
        """Normalize and clean raw text into tokens.

        Args:
            raw_text: The raw input text to tokenize.

        Returns:
            A list of cleaned tokens with stop words and short tokens removed.
        """
        if not raw_text:
            return []

        text = CAMEL_CASE_LOWER_TO_UPPER.sub(r'\1 \2', raw_text)
        text = CAMEL_CASE_ACRONYM_TO_WORD.sub(r'\1 \2', text)
        cleaned_text = NON_ALPHANUMERIC.sub(' ', text)

        lower_text = cleaned_text.lower()

        tokens = lower_text.split()
        clean_tokens = []

        for token in tokens:
            if token in self.stop_words:
                continue
            if len(token) <= 2:
                continue

            clean_tokens.append(token)

        return clean_tokens

    def get_terms_frequency_in_one_chunk(
        self,
        clean_tokens: List[str],
    ) -> dict[str, int]:
        """Compute term frequency for a single token list.

        Args:
            clean_tokens: A list of cleaned tokens.

        Returns:
            A dictionary mapping each token to its frequency count.
        """
        terms_frequency_dict = Counter(clean_tokens)
        return terms_frequency_dict

    def get_document_frequency(
        self,
        all_term_frequencies: list[dict[str, int]],
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
