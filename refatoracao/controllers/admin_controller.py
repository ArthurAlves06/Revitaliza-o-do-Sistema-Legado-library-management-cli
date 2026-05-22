import datetime
import logging
import smtplib

from rich.console import Console
from rich.table import Table

from config import LOAN_DAYS, FINE_PER_DAY
from models.book import Book
from repositories.book_repository import BookRepository
from repositories.account_repository import AccountRepository
from utils.mail import MailService
from utils.utils import check_internet

logger = logging.getLogger(__name__)
console = Console()


class AdminController:
    """
    Controlador do administrador.
    Orquestra lógica de negócio sem conhecer detalhes de SQL ou de apresentação.
    Substitui o script procedural admin.py (God Class).
    """

    def __init__(
        self,
        book_repo: BookRepository,
        account_repo: AccountRepository,
        mail_service: MailService,
    ):
        self._books = book_repo
        self._accounts = account_repo
        self._mail = mail_service

    # ──────────────────────────────────────────────────────────
    # MENU
    # ──────────────────────────────────────────────────────────

    def run_menu(self) -> None:
        while True:
            console.print("\n[red]LIPS Library Management System[/red]", justify="center")
            console.print("1. [green]Issue Book")
            console.print("2. [green]Return Book")
            console.print("3. [green]Search Book")
            console.print("4. [green]List Books")
            console.print("5. [green]Add Book")
            console.print("6. [green]Edit Book")
            console.print("7. [green]Delete Book")
            console.print("8. [green]Student Info")
            console.print("9. [green]Exit")

            ch = input("Enter >> ").strip()

            actions = {
                "1": self._handle_issue,
                "2": self._handle_return,
                "3": self._handle_search,
                "4": self._handle_list,
                "5": self._handle_add,
                "6": self._handle_edit,
                "7": self._handle_delete,
                "8": self._handle_student_info,
                "9": lambda: None,
            }

            if ch == "9":
                break
            action = actions.get(ch)
            if action:
                action()
            else:
                console.print("[red]Opção inválida.[/]")

    # ──────────────────────────────────────────────────────────
    # CASOS DE USO
    # ──────────────────────────────────────────────────────────

    def issue_book(self, book_id: int, student_id: int) -> bool:
        """
        Caso de uso: emitir livro para aluno.
        Retorna True se bem-sucedido.
        """
        book = self._books.find_available(book_id)
        if book is None:
            console.print("[red]Livro não disponível ou não encontrado.[/]")
            return False

        student = self._accounts.find_by_id(student_id)
        if student is None:
            console.print("[red]Aluno não encontrado.[/]")
            return False

        if book.is_reserved:
            console.print("[yellow]Este livro está reservado por alguém![/]")
            confirm = input("Deseja emitir mesmo assim? (yes/no) > ")
            if confirm.lower() not in ("yes", "y", "sim", "s"):
                return False

        today = datetime.date.today()
        self._books.issue_book(book_id, student_id, str(today))
        console.print(f"[green]Livro emitido para {student.username}![/]")
        logger.info("Livro %s emitido para aluno %s", book_id, student_id)

        if check_internet():
            self._send_issue_email(student, book, today)
        else:
            console.print("[yellow]Sem internet — e-mail não enviado.[/]")

        return True

    def return_book(self, book_id: int) -> bool:
        """Caso de uso: devolver livro e calcular multa."""
        book = self._books.find_by_id(book_id)
        if book is None or book.is_available:
            console.print("[yellow]Livro não está emitido.[/]")
            return False

        days = self._days_since(book.issue_date)
        fine = max(0.0, (days - LOAN_DAYS) * FINE_PER_DAY)

        self._books.return_book(book_id)
        self._accounts.add_fine(book.issued_to, fine)

        student = self._accounts.find_by_id(book.issued_to)
        console.print(f"[green]Livro devolvido! Multa gerada: R$ {fine:.2f}[/]")
        logger.info("Livro %s devolvido. Multa: %.2f", book_id, fine)

        if student and check_internet():
            self._send_return_email(student, book, fine)

        return True

    def search_book(self, book_id: int) -> None:
        book = self._books.find_by_id(book_id)
        if book is None:
            console.print("[red]Livro não encontrado.[/]")
            return

        self._print_book(book)
        if not book.is_available:
            student = self._accounts.find_by_id(book.issued_to)
            name = student.username if student else "Desconhecido"
            console.print(f"[green]Emitido para: {name} | Data: {book.issue_date}[/]")
        else:
            console.print("[green]Disponível[/]")

    def list_books(self) -> None:
        books = self._books.find_all()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Título")
        table.add_column("Autor", justify="right")
        table.add_column("Preço", justify="right")
        table.add_column("Emitido Para", justify="right")
        table.add_column("Data Emissão", justify="right")

        for book in books:
            if not book.is_available:
                student = self._accounts.find_by_id(book.issued_to)
                issued_name = student.username if student else "?"
            else:
                issued_name = "Disponível"

            table.add_row(
                str(book.id),
                book.title,
                book.author,
                f"R$ {book.price:.2f}",
                issued_name,
                str(book.issue_date or "-"),
            )

        console.print(table)

    def add_book(self, book_id: int, title: str, author: str, price: float) -> bool:
        if self._books.id_exists(book_id):
            console.print("[yellow]Já existe um livro com este ID.[/]")
            return False

        book = Book(id=book_id, title=title, author=author, price=price)
        self._books.add(book)
        console.print("[green]Livro adicionado com sucesso![/]")
        return True

    def edit_book(self, book_id: int, title: str = None, author: str = None, price: float = None) -> bool:
        book = self._books.find_by_id(book_id)
        if book is None:
            console.print("[red]Livro não encontrado.[/]")
            return False

        if title:
            book.title = title
        if author:
            book.author = author
        if price is not None:
            book.price = price

        self._books.update(book)
        console.print("[green]Livro atualizado com sucesso![/]")
        return True

    def delete_book(self, book_id: int) -> bool:
        book = self._books.find_by_id(book_id)
        if book is None:
            console.print("[red]Livro não encontrado.[/]")
            return False

        self._books.delete(book_id)
        console.print("[red]Livro removido com sucesso.[/]")
        return True

    def student_info(self, student_id: int) -> None:
        student = self._accounts.find_by_id(student_id)
        if student is None:
            console.print("[red]Aluno não encontrado.[/]")
            return

        console.print(f"[cyan]Usuário:[/] {student.username}")
        console.print(f"[cyan]E-mail:[/]  {student.email}")
        console.print(f"[cyan]Multa:[/]   R$ {student.amount:.2f}")

    # ──────────────────────────────────────────────────────────
    # HANDLERS DO MENU (Long Method extraído em métodos menores)
    # ──────────────────────────────────────────────────────────

    def _handle_issue(self) -> None:
        while True:
            try:
                student_id = int(input("ID do aluno > "))
                book_id = int(input("ID do livro > "))
            except ValueError:
                console.print("[red]ID inválido.[/]")
                continue

            self.issue_book(book_id, student_id)

            if input("Emitir mais? (y/n) > ").lower() in ("n", "não", "nao"):
                break

    def _handle_return(self) -> None:
        while True:
            try:
                book_id = int(input("ID do livro > "))
            except ValueError:
                console.print("[red]ID inválido.[/]")
                continue

            self.return_book(book_id)

            if input("Devolver mais? (y/n) > ").lower() in ("n", "não", "nao"):
                break

    def _handle_search(self) -> None:
        try:
            book_id = int(input("ID do livro > "))
            self.search_book(book_id)
        except ValueError:
            console.print("[red]ID inválido.[/]")

    def _handle_list(self) -> None:
        self.list_books()

    def _handle_add(self) -> None:
        while True:
            try:
                book_id = int(input("ID do livro > "))
                title = input("Título > ")
                author = input("Autor > ")
                price = float(input("Preço > "))
            except ValueError:
                console.print("[red]Valor inválido.[/]")
                continue

            self.add_book(book_id, title, author, price)

            if input("Adicionar mais? (y/n) > ").lower() in ("n", "não", "nao"):
                break

    def _handle_edit(self) -> None:
        try:
            book_id = int(input("ID do livro > "))
        except ValueError:
            console.print("[red]ID inválido.[/]")
            return

        book = self._books.find_by_id(book_id)
        if not book:
            console.print("[red]Livro não encontrado.[/]")
            return

        self._print_book(book)
        console.print("O que deseja editar?\n1. Título  2. Autor  3. Preço")
        ch = input("> ").strip()

        title = author = None
        price = None

        if ch == "1":
            title = input("Novo título > ")
        elif ch == "2":
            author = input("Novo autor > ")
        elif ch == "3":
            try:
                price = float(input("Novo preço > "))
            except ValueError:
                console.print("[red]Preço inválido.[/]")
                return
        else:
            console.print("[red]Opção inválida.[/]")
            return

        self.edit_book(book_id, title, author, price)

    def _handle_delete(self) -> None:
        while True:
            try:
                book_id = int(input("ID do livro > "))
            except ValueError:
                console.print("[red]ID inválido.[/]")
                continue

            book = self._books.find_by_id(book_id)
            if not book:
                console.print("[red]Livro não encontrado.[/]")
            else:
                self._print_book(book)
                confirm = input('Tem certeza? Digite "yes" para confirmar > ')
                if confirm.lower() == "yes":
                    self.delete_book(book_id)

            if input("Deletar mais? (y/n) > ").lower() in ("n", "não", "nao"):
                break

    def _handle_student_info(self) -> None:
        try:
            student_id = int(input("ID do aluno > "))
            self.student_info(student_id)
        except ValueError:
            console.print("[red]ID inválido.[/]")

    # ──────────────────────────────────────────────────────────
    # HELPERS PRIVADOS
    # ──────────────────────────────────────────────────────────

    def _send_issue_email(self, student, book, today: datetime.date) -> None:
        return_date = today + datetime.timedelta(days=LOAN_DAYS)
        try:
            self._mail.send_issue(
                student.email, book.id, book.title,
                book.author, str(return_date), student.username,
            )
            logger.info("E-mail de emissão enviado para %s", student.email)
        except ConnectionError as e:
            logger.warning("Falha de conexão SMTP: %s", e)
            console.print("[red]Sem conexão para enviar e-mail.[/]")
        except smtplib.SMTPAuthenticationError as e:
            logger.error("Credenciais SMTP inválidas: %s", e)
            console.print("[red]Erro de autenticação no servidor de e-mail.[/]")
        except Exception as e:
            logger.exception("Erro inesperado ao enviar e-mail de emissão: %s", e)
            console.print("[red]Erro inesperado. Veja library.log para detalhes.[/]")

    def _send_return_email(self, student, book, fine: float) -> None:
        try:
            self._mail.send_ret(
                student.email, book.id, book.title,
                book.author, str(datetime.date.today()),
                student.username, student.amount, fine,
            )
            logger.info("E-mail de devolução enviado para %s", student.email)
        except ConnectionError as e:
            logger.warning("Falha de conexão SMTP: %s", e)
            console.print("[red]Sem conexão para enviar e-mail.[/]")
        except Exception as e:
            logger.exception("Erro inesperado ao enviar e-mail de devolução: %s", e)
            console.print("[red]Erro ao enviar e-mail. Veja library.log.[/]")

    @staticmethod
    def _print_book(book: Book) -> None:
        console.print(
            f"[cyan]ID:[/] {book.id} | [cyan]Título:[/] {book.title} | "
            f"[cyan]Autor:[/] {book.author} | [cyan]Preço:[/] R$ {book.price:.2f}"
        )

    @staticmethod
    def _days_since(date_str: str) -> int:
        issue = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.datetime.now() - issue).days
