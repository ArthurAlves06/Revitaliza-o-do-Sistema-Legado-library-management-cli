import sqlite3
import unittest

from models.book import Book
from repositories.book_repository import BookRepository


def _make_db() -> sqlite3.Connection:
    """Cria banco em memória para testes — sem tocar no database.db real."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE BOOKS (
            ID INTEGER PRIMARY KEY,
            TITLE CHAR NOT NULL,
            AUTHOR CHAR NOT NULL,
            PRICE NUMERIC NOT NULL,
            ISSUED_TO INTEGER DEFAULT 0,
            ISSUE_DATE DATE,
            RESERVED INTEGER DEFAULT 0
        )"""
    )
    conn.commit()
    return conn


class TestBookRepository(unittest.TestCase):

    def setUp(self):
        self.conn = _make_db()
        self.repo = BookRepository(self.conn)
        self.sample = Book(id=1, title="Clean Code", author="Robert Martin", price=79.90)

    def tearDown(self):
        self.conn.close()

    def test_add_and_find_by_id(self):
        self.repo.add(self.sample)
        book = self.repo.find_by_id(1)
        self.assertIsNotNone(book)
        self.assertEqual(book.title, "Clean Code")

    def test_find_by_id_not_found(self):
        result = self.repo.find_by_id(999)
        self.assertIsNone(result)

    def test_find_available_returns_book_when_free(self):
        self.repo.add(self.sample)
        book = self.repo.find_available(1)
        self.assertIsNotNone(book)

    def test_find_available_returns_none_when_issued(self):
        self.repo.add(self.sample)
        self.repo.issue_book(1, student_id=42, issue_date="2026-01-01")
        book = self.repo.find_available(1)
        self.assertIsNone(book)

    def test_issue_and_return_book(self):
        self.repo.add(self.sample)
        self.repo.issue_book(1, student_id=42, issue_date="2026-01-01")

        issued = self.repo.find_by_id(1)
        self.assertEqual(issued.issued_to, 42)

        self.repo.return_book(1)
        returned = self.repo.find_by_id(1)
        self.assertEqual(returned.issued_to, 0)
        self.assertIsNone(returned.issue_date)

    def test_delete(self):
        self.repo.add(self.sample)
        self.repo.delete(1)
        self.assertIsNone(self.repo.find_by_id(1))

    def test_id_exists(self):
        self.assertFalse(self.repo.id_exists(1))
        self.repo.add(self.sample)
        self.assertTrue(self.repo.id_exists(1))

    def test_find_all(self):
        self.repo.add(self.sample)
        self.repo.add(Book(id=2, title="Refactoring", author="Martin Fowler", price=99.00))
        books = self.repo.find_all()
        self.assertEqual(len(books), 2)

    def test_sql_injection_safe(self):
        """Garante que queries parametrizadas não são vulneráveis a injeção."""
        self.repo.add(self.sample)
        # Tentativa de SQL injection no book_id — deve retornar None sem erro
        result = self.repo.find_by_id("1 OR 1=1")  # type: ignore
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
