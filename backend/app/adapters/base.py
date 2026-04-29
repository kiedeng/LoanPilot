from abc import ABC, abstractmethod
from typing import Any


class BankingAdapter(ABC):
    @abstractmethod
    def query_loan_products(self, segment: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def pre_assess_credit_limit(self, profile: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_loan_application(self, user_id: int, product_id: str, amount: float, purpose: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def query_application_status(self, application_id: str) -> dict[str, Any]:
        raise NotImplementedError
