from litellm import completion


class LLMAuditor:
    def __init__(self, *, model: str, timeout_s: int = 30, temperature: float = 0.0) -> None:
        self.model = model
        self.timeout_s = timeout_s
        self.temperature = temperature

    def audit(self, *, prompt: str, nonce: str) -> str:
        resp = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            timeout=self.timeout_s,
            temperature=self.temperature,
        )
        return str(resp.choices[0].message.content)
