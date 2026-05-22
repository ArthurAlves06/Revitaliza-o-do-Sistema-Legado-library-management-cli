import sqlite3
import logging
from typing import Optional, List

from models.book import Book

logger = logging.getLogger(__name__)


class BookRepository:
    """
    Acesso ao banco para a entidade Book.
    Única camada que toca SQL — todas as queries são parametrizadas (sem SQL Injection).
    """

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection
        self._cur = connection.cursor()

    def find_by_id(self, book_id: int) -> Optional[Book]:
        self._cur.execute("SELECT * FROM BOOKS WHERE ID = ?", (book_id,))
        row = self._cur.fetchone()
        return self._row_to_book(row) if row else None

    def find_available(self, book_id: int) -> Optional[Book]:
        """Retorna o livro somente se existir E estiver disponível."""
        self._cur.execute(
            "SELECT * FROM BOOKS WHERE ID = ? AND ISSUED_TO = 0",
            (book_id,),
        )
        row = self._cur.fetchone()
        return self._row_to_book(row) if row else None

    def find_all(self) -> List[Book]:
        self._cur.execute("SELECT * FROM BOOKS")
        return [self._row_to_book(r) for r in self._cur.fetchall()]

    def add(self, book: Book) -> None:
        self._cur.execute(
            "INSERT INTO BOOKS (ID, TITLE, AUTHOR, PRICE) VALUES (?, ?, ?, ?)",
            (book.id, book.title, book.author, book.price),
        )
        self._conn.commit()
        logger.info("Livro adicionado: ID=%s TITLE=%s", book.id, book.title)

    def update(self, book: Book) -> None:
        self._cur.execute(
            "UPDATE BOOKS SET TITLE = ?, AUTHOR = ?, PRICE = ? WHERE ID = ?",
            (book.title, book.author, book.price, book.id),
        )
        self._conn.commit()

    def delete(self, book_id: int) -> None:
        self._cur.execute("DELETE FROM BOOKS WHERE ID = ?", (book_id,))
        self._conn.commit()
        logger.info("Livro removido: ID=%s", book_id)

    def issue_book(self, book_id: int, student_id: int, issue_date: str) -> None:
        self._cur.execute(
            "UPDATE BOOKS SET ISSUED_TO = ?, ISSUE_DATE = ?, RESERVED = 0 WHERE ID = ?",
            (student_id, issue_date, book_id),
        )
        self._conn.commit()

    def return_book(self, book_id: int) -> None:
        self._cur.execute(
            "UPDATE BOOKS SET ISSUED_TO = 0, ISSUE_DATE = NULL WHERE ID = ?",
            (book_id,),
        )
        self._conn.commit()

    def id_exists(self, book_id: int) -> bool:
        self._cur.execute("SELECT 1 FROM BOOKS WHERE ID = ?", (book_id,))
        return self._cur.fetchone() is not None

    @staticmethod
    def _row_to_book(row: tuple) -> Book:
        return Book(
            id=row[0],
            title=row[1],
            author=row[2],
            price=row[3],
            issued_to=row[4],
            issue_date=row[5],
            reserved=row[6],
        )
