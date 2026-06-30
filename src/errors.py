# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  errors.py                                         :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: stephanie <stephanie@student.42.fr>       +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/06/30 11:39:42 by stephanie       #+#    #+#               #
#  Updated: 2026/06/30 13:47:24 by stephanie       ###   ########.fr        #
#                                                                           #
# ************************************************************************* #
"""Module defining custom exceptions for the RAG."""
from pydantic import ValidationError


class RagError(Exception):
    """Base class for all exceptions in the program.

    Attributes:
        message (str) : A descriptive error message.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message


class RagLoadError(RagError):
    """Exception raised when a file fails to load due to system errors."""
    def __str__(self) -> str:
        """
        Return the formatted error message.

        Returns:
            str: A string tagged with [SYSTEM ERROR].
        """
        return f"[SYSTEM ERROR] {self.message}"


class RagValidationError(RagError):
    """Exception raised for Pydantic data structure validation failures.

    Attributes:
        path_name (str): The name of the file that failed validation.
        pydantic_error (ValidationError): The raw Pydantic exception.
    """
    def __init__(
            self, path_name: str, pydantic_error: ValidationError
            ) -> None:
        """Initialize RagValidationError with path and pydantic error."""
        self.path_name = path_name
        self.pydantic_error = pydantic_error
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Extract and clean all error messages from Pydantic.

        Returns:
            str: A comprehensive, cleaned-up error string.
        """
        clean_errors = []
        for error in self.pydantic_error.errors():
            location = "->".join(str(loc) for loc in error.get("loc", []))
            raw_msg = error.get("msg", "Unknown error")
            clean_msg = raw_msg.replace("Value error,", "")
            clean_errors.append(f" Field {location}: {clean_msg}")
        formatted_errors = "\n".join(clean_errors)
        return (
            f"Data structure validation failed for '{self.path_name}'.\n"
            f"{formatted_errors}")

    def __str__(self) -> str:
        """
        Return the formatted error message.

        Returns:
            str: A string tagged with [PYDANTIC ERROR].
        """
        return f"[PYDANTIC ERROR] {self.message}"
