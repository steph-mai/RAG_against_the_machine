"""Data models for RAG application using Pydantic."""

from pydantic import BaseModel, Field
from typing import List
import uuid


class MinimalSource(BaseModel):
    """Represents the location of a source in a document.

    Attributes:
        file_path: Path to the source file.
        first_character_index: Index of the first character of the source span.
        last_character_index: Index of the last character of the source span.
    """

    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """Represents a question without an answer.

    Attributes:
        question_id: Unique identifier for the question.
        question: Text of the question.
    """

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Represents a question with an answer and associated sources.

    Attributes:
        sources: List of minimal source references for the answer.
        answer: Text of the answer.
    """

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Represents a dataset of questions for RAG tasks.

    Attributes:
        rag_questions: List of answered or unanswered questions.
    """

    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Represents the results of a search for a specific question.

    Attributes:
        question_id: Identifier of the original question.
        question: Text of the original question.
        retrieved_sources: List of sources retrieved during the search.
    """

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Represents a search result that includes an answer.

    Attributes:
        answer: Text of the answer.
    """

    answer: str


class StudentSearchResults(BaseModel):
    """Represents student search results without answers.

    Attributes:
        search_results: List of minimal search results.
        k: Number of results requested or returned.
    """

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """Represents student search results including answers.

    Attributes:
        search_results: List of minimal answers.
        k: Number of results requested or returned.
    """

    search_results: List[MinimalAnswer]
    k: int
