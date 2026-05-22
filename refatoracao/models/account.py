from dataclasses import dataclass
from typing import Optional


@dataclass
class Account:
    """Entidade Conta (admin ou aluno)."""
    id: int
    type: str          # 'A' = Admin, 'S' = Student
    username: str
    password: str
    amount: float = 0.0
    email: str = ""
    link_id: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.type == "A"
