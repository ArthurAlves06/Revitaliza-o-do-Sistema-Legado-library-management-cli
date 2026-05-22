import sqlite3
import logging
from typing import Optional

from models.account import Account

logger = logging.getLogger(__name__)


class AccountRepository:
    """
    Acesso ao banco para a entidade Account.
    Todas as queries são parametrizadas — sem SQL Injection.
    """

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection
        self._cur = connection.cursor()

    def find_by_id(self, account_id: int) -> Optional[Account]:
        self._cur.execute("SELECT * FROM ACCOUNTS WHERE ID = ?", (account_id,))
        row = self._cur.fetchone()
        return self._row_to_account(row) if row else None

    def find_by_username(self, username: str) -> Optional[Account]:
        self._cur.execute(
            "SELECT * FROM ACCOUNTS WHERE USERNAME = ?", (username,)
        )
        row = self._cur.fetchone()
        return self._row_to_account(row) if row else None

    def create(self, account: Account) -> None:
        self._cur.execute(
            "INSERT INTO ACCOUNTS (TYPE, USERNAME, PASSWORD, EMAIL) VALUES (?, ?, ?, ?)",
            (account.type, account.username, account.password, account.email),
        )
        self._conn.commit()
        logger.info("Conta criada: USERNAME=%s", account.username)

    def update_email(self, account_id: int, new_email: str) -> None:
        self._cur.execute(
            "UPDATE ACCOUNTS SET EMAIL = ? WHERE ID = ?",
            (new_email, account_id),
        )
        self._conn.commit()

    def update_password(self, account_id: int, new_password: str) -> None:
        self._cur.execute(
            "UPDATE ACCOUNTS SET PASSWORD = ? WHERE ID = ?",
            (new_password, account_id),
        )
        self._conn.commit()

    def add_fine(self, account_id: int, fine: float) -> None:
        self._cur.execute(
            "UPDATE ACCOUNTS SET AMMOUNT = AMMOUNT + ? WHERE ID = ?",
            (fine, account_id),
        )
        self._conn.commit()

    def clear_fine(self, account_id: int) -> None:
        self._cur.execute(
            "UPDATE ACCOUNTS SET AMMOUNT = 0 WHERE ID = ?",
            (account_id,),
        )
        self._conn.commit()

    def username_exists(self, username: str) -> bool:
        self._cur.execute(
            "SELECT 1 FROM ACCOUNTS WHERE USERNAME = ?", (username,)
        )
        return self._cur.fetchone() is not None

    @staticmethod
    def _row_to_account(row: tuple) -> Account:
        return Account(
            id=row[0],
            type=row[1],
            username=row[2],
            password=row[3],
            amount=row[4],
            email=row[5],
            link_id=row[6],
        )
