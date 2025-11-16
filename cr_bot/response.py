import json5
from loguru import logger


class ResponseManager:
    def __init__(self, json5_path: str):
        self.json5_path = json5_path
        self.responses: list[dict] = []
        self.load()

    def load(self) -> None:
        try:
            with open(self.json5_path, "r", encoding="utf-8") as f:
                self.responses = json5.load(f)
        except FileNotFoundError:
            logger.warning(
                f"{self.json5_path} not found. Starting with empty responses."
            )
            self.responses = []

    def save(self) -> None:
        try:
            with open(self.json5_path, "w", encoding="utf-8") as f:
                json5.dump(self.responses, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save responses: {e}")

    def add(self, trigger: str, response: str) -> None:
        self.responses.append({"trigger": trigger, "response": response})
        self.save()

    def remove(self, id: int) -> None:
        if 0 <= id < len(self.responses):
            self.responses.pop(id)
            self.save()
        else:
            raise IndexError("Response ID out of range")

    def list(self) -> list[dict]:
        return self.responses

    def get(self, id: int) -> dict | None:
        if 0 <= id < len(self.responses):
            return self.responses[id]
        raise IndexError("Response ID out of range")
