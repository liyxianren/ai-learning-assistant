"""Schemas for request validation."""

from .auth import LoginSchema, RegisterSchema
from .history import HistoryQuerySchema
from .problem import ParseSchema, RecognizeSchema, SolveProblemSchema, SolveSchema, SolveStreamSchema

__all__ = [
    "RegisterSchema",
    "LoginSchema",
    "RecognizeSchema",
    "ParseSchema",
    "SolveSchema",
    "SolveProblemSchema",
    "SolveStreamSchema",
    "HistoryQuerySchema",
]
