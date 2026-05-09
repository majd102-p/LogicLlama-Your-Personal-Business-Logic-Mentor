"""Simple query helpers for the first retrieval layer."""

from __future__ import annotations

from src.core import LogicCase, QueryFilter, SQLiteLogicStore


class LogicSearchService:
    """Keyword and taxonomy search over normalized cases."""

    def __init__(self, store: SQLiteLogicStore) -> None:
        self.store = store

    def search(self, text: str | None = None, limit: int = 20) -> list[LogicCase]:
        return self.store.search_cases(QueryFilter(text=text, limit=limit))

    def get_case(self, pattern_id: str) -> LogicCase | None:
        return self.store.get_case(pattern_id)
