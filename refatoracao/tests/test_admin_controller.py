import sqlite3
import unittest
from unittest.mock import MagicMock, patch

from models.book import Book
from models.account import Account
from repositories.book_repository import BookRepository
from repositories.account_repository import AccountRepository
from controllers.admin_controller import AdminController


def _make_db() -> sqlite3.Connection:
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
    conn.execute(
        """CREATE TABLE ACCOUNTS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TYPE VARCHAR(1),
            USERNAME VARCHAR(20),
            PASSWORD VARCHAR(64),
            AMMOUNT NUMERIC DEFAULT 0,
            EMAIL CHAR(32),
            LINKID CHAR
        )"""
    )
    conn.commit()
    return conn


class TestAdminController(unittest.TestCase):

    def setUp(self):
        self.conn = _make_db()
        self.book_repo = BookRepository(self.conn)
        self.account_repo = AccountRepository(self.conn)
        self.mail = MagicMock()  # Mail mockado — sem envio real de e-mail

        self.controller = AdminController(self.book_repo, self.account_repo, self.mail)

        # Fixtures
        self.book_repo.add(Book(id=1, title="Clean Code", author="R. Martin", price=79.90))
        self.conn.execute(
            "INSERT INTO ACCOUNTS (TYPE, USERNAME, PASSWORD, AMMOUNT, EMAIL) VALUES (?,?,?,?,?)",
            ("S", "joao", "hashed", 0, "joao@example.com"),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    @patch("controllers.admin_controller.check_internet", return_value=False)
    def test_issue_book_success(self, _mock_internet):
        student = self.account_repo.find_by_username("joao")
        result = self.controller.issue_book(book_id=1, student_id=student.id)

        self.assertTrue(result)
        book = self.book_repo.find_by_id(1)
        self.assertEqual(book.issued_to, student.id)

    @patch("controllers.admin_controller.check_internet", return_value=False)
    def test_issue_book_unavailable(self, _mock_internet):
        student = self.account_repo.find_by_username("joao")
        self.controller.issue_book(book_id=1, student_id=student.id)  # 1ª emissão

        result = self.controller.issue_book(book_id=1, student_id=student.id)  # 2ª tentativa
        self.assertFalse(result)

    @patch("controllers.admin_controller.check_internet", return_value=False)
    def test_return_book_applies_fine(self, _mock_internet):
        student = self.account_repo.find_by_username("joao")
        # Emite com data antiga para gerar multa
        self.book_repo.issue_book(1, student.id, "2025-01-01")

        result = self.controller.return_book(book_id=1)
        self.assertTrue(result)

        updated = self.account_repo.find_by_id(student.id)
        self.assertGreater(updated.amount, 0)  # Multa foi aplicada

    def test_return_book_not_issued(self):
        result = self.controller.return_book(book_id=1)
        self.assertFalse(result)

    def test_add_book_success(self):
        result = self.controller.add_book(99, "Novo Livro", "Autor X", 49.90)
        self.assertTrue(result)
        self.assertIsNotNone(self.book_repo.find_by_id(99))

    def test_add_book_duplicate_id(self):
        result = self.controller.add_book(1, "Duplicado", "Autor", 10.0)
        self.assertFalse(result)

    def test_delete_book(self):
        result = self.controller.delete_book(book_id=1)
        self.assertTrue(result)
        self.assertIsNone(self.book_repo.find_by_id(1))

    def test_delete_nonexistent_book(self):
        result = self.controller.delete_book(book_id=999)
        self.assertFalse(result)

    @patch("controllers.admin_controller.check_internet", return_value=True)
    def test_issue_sends_email_when_online(self, _mock_internet):
        student = self.account_repo.find_by_username("joao")
        self.controller.issue_book(book_id=1, student_id=student.id)
        self.mail.send_issue.assert_called_once()


if __name__ == "__main__":
    unittest.main()
