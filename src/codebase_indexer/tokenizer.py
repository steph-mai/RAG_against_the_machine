# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  tokenizer.py                                      :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 16:41:18 by stephanie       #+#    #+#               #
#  Updated: 2026/07/23 17:06:25 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

import re
from typing import List, Any
from collections import Counter


class Tokenizer():
    def __init__(self):
        self.stop_words: set[str] = {
            "the", "a", "an", "and", "or", "but", "if", "then", "else",
            "for", "in", "is", "are", "to", "of", "it", "on", "with", "as",
            "this", "that", "by", "from", "at",
            "def", "class", "self", "return", "import", "from", "pass"
        }

    def normalize_and_clean_raw_text(self, raw_text: str) -> List[str]:
        pass

    def get_term_frequency_in_one_chunk(
            self, clean_tokens: List[str]) -> dict[str, int]:
        # use Counter
        pass

    def get_document_frequency(
            self, all_term_frequencies: list[dict[str, int]]
            ) -> dict[str, int]:
        pass
