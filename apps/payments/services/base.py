from abc import ABC, abstractmethod
from typing import Iterator


class BasePaymentProvider(ABC):
    @abstractmethod
    def fetch_payments(self, limit: int = 100, starting_after: str | None = None) -> list[dict]:
        pass

    @abstractmethod
    def get_all_payments(self) -> Iterator[dict]:
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        pass
