from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Book:
    """Entidade Livro — representa apenas os dados, sem lógica de banco."""
    id: int
    title: str
    author: str
    price: float
    issued_to: int = 0
    issue_date: Optional[str] = None
    reserved: int = 0

    @property
    def is_available(self) -> bool:
        return self.issued_to == 0

    @property
    def is_reserved(self) -> bool:
        return self.reserved != 0
