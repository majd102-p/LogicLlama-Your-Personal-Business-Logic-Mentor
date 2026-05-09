#!/usr/bin/env python
"""Run a tiny RAG MVP demonstration using the local store."""

from src.core.settings import get_settings
from src.core.storage import SQLiteLogicStore
from src.rag.mvp import RAGService


def main():
    settings = get_settings()
    store = SQLiteLogicStore(settings.database_path)
    store.initialize()

    rag = RAGService(store)
    query = input("Enter a short search query: ")
    print(rag.answer(query))


if __name__ == '__main__':
    main()
