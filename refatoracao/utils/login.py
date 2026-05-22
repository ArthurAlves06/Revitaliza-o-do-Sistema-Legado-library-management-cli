import hashlib
import logging
from typing import Optional

from rich.console import Console

from config import ADMIN_USERNAME, ADMIN_PASSWORD
from models.account import Account
from repositories.account_repository import AccountRepository

logger = logging.getLogger(__name__)
console = Console()


class LoginService:
    """
    Serviço de autenticação.
    Elimina data.pickle e os.system — retorna objeto Account diretamente.
    Magic Numbers (credenciais hardcoded) movidos para config.py / .env.
    """

    def __init__(self, account_repo: AccountRepository):
        self._accounts = account_repo

    def authenticate(self) -> Optional[Account]:
        """
        Apresenta tela de login e retorna a conta autenticada.
        Retorna None se o usuário cancelar.
        """
        console.print("\n[red]LIPS Library Management System[/]", justify="center")
        console.print("1. [green]Admin")
        console.print("2. [green]Aluno")
        console.print("3. [green]Sair")

        ch = input("Selecione seu perfil >> ").strip()

        if ch == "1":
            return self._admin_login()
        elif ch == "2":
            return self._student_login()
        else:
            return None

    def _admin_login(self) -> Optional[Account]:
        username = input("Usuário admin > ").strip()
        password = input("Senha > ").strip()

        # Credenciais vindas do .env via config.py — não hardcoded
        if username == ADMIN_USERNAME and self._admin_password_matches(password):
            logger.info("Admin autenticado: %s", username)
            return Account(id=0, type="A", username=username, password="")
        else:
            console.print("[red]Credenciais inválidas.[/]")
            logger.warning("Tentativa de login admin falhou para usuário: %s", username)
            return None

    def _student_login(self) -> Optional[Account]:
        console.print("1. Login  2. Cadastro  3. Redefinir Senha")
        ch = input("> ").strip()

        if ch == "1":
            return self._student_authenticate()
        elif ch == "2":
            return self._student_register()
        elif ch == "3":
            self._student_reset_password()
            return None
        return None

    def _student_authenticate(self) -> Optional[Account]:
        username = input("Usuário > ").strip()
        password = input("Senha > ").strip()

        account = self._accounts.find_by_username(username)
        if account is None:
            console.print("[red]Usuário não encontrado.[/]")
            return None

        if not self._check_password(password, account.password):
            console.print("[red]Senha incorreta.[/]")
            logger.warning("Tentativa de login falhou para usuário: %s", username)
            return None

        logger.info("Aluno autenticado: %s (ID=%s)", username, account.id)
        return account

    def _student_register(self) -> Optional[Account]:
        username = input("Nome de usuário > ").strip()
        if self._accounts.username_exists(username):
            console.print("[red]Nome de usuário já existe.[/]")
            return None

        email = input("E-mail > ").strip()
        password = input("Senha > ").strip()

        hashed = self._hash_password(password)
        new_account = Account(id=0, type="S", username=username, password=hashed, email=email)
        self._accounts.create(new_account)

        console.print("[green]Conta criada! Faça login para continuar.[/]")
        logger.info("Nova conta criada: %s", username)
        return None

    def _student_reset_password(self) -> None:
        username = input("Usuário > ").strip()
        account = self._accounts.find_by_username(username)
        if account is None:
            console.print("[red]Usuário não encontrado.[/]")
            return

        new_password = input("Nova senha > ").strip()
        hashed = self._hash_password(new_password)
        self._accounts.update_password(account.id, hashed)
        console.print("[green]Senha redefinida com sucesso![/]")

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _check_password(plain: str, stored: str) -> bool:
        return hashlib.sha256(plain.encode()).hexdigest() == stored

    @staticmethod
    def _admin_password_matches(plain: str) -> bool:
        return plain == ADMIN_PASSWORD or hashlib.sha256(plain.encode()).hexdigest() == ADMIN_PASSWORD
