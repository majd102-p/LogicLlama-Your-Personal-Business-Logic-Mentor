from typing import List

from src.rag import LogicSearchService


class RAGService:
    """Very small RAG MVP that retrieves relevant cases and synthesizes a short summary.

    This MVP does not call an LLM by default — it returns a synthesized summary
    from retrieved case titles and focuses. Provide an `llm_client` that implements
    `generate(prompt: str) -> str` to perform real LLM responses.
    """

    def __init__(self, store):
        self.store = store
        self.search = LogicSearchService(store)

    def retrieve(self, query: str, limit: int = 5) -> List[dict]:
        results = self.search.search(query, limit=limit)
        out = []
        for c in results:
            out.append({
                "pattern_id": c.pattern_id,
                "title": c.title,
                "focus": getattr(c, "focus", None),
                "confidence": getattr(c, "confidence", None),
            })
        return out

    def answer(self, query: str, llm_client=None) -> str:
        hits = self.retrieve(query, limit=5)
        if not hits:
            return "No relevant cases found."

        summary_lines = [f"Top {len(hits)} cases for '{query}':"]
        for h in hits:
            summary_lines.append(f"- {h['pattern_id']}: {h['title']} (focus={h.get('focus')})")

        prompt = "\n".join(summary_lines)

        if llm_client is not None:
            try:
                return llm_client.generate(prompt)
            except Exception:
                # Fallback
                return prompt

        return prompt
