# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  logger.py                                         :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stmaire <stmaire@student.42.fr>           +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/07/23 10:21:19 by stephanie       #+#    #+#               #
#  Updated: 2026/08/06 11:46:47 by stmaire         ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

"""
Logger setup utilities.

This module provides a helper to configure the root logger
with a stream handler.
"""

import logging


def get_logger(name: str = "rag") -> logging.Logger:
    """Configure the logger with dual handlers (console and file).

    - Console: Clean output for CLI users (just the message).
    - File: Detailed timestamped logs in `rag_debug.log` for developers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter())
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(
            "rag_debug.log", mode="a", encoding="utf-8")
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


logger = get_logger()
