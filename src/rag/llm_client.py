class LLMClient:
    """Minimal LLM client interface.

    Implement `generate(prompt: str) -> str` in a subclass to connect to a real model.
    """

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("LLMClient.generate must be implemented by a concrete client")
