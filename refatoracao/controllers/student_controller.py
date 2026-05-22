import logging

from rich.console import Console

from repositories.book_repository import BookRepository
from repositories.account_repository import AccountRepository
from utils.mail import MailService
from utils.utils import check_internet

logger = logging.getLogger(__name__)
console = Console()


class StudentController:
    """
    Controlador do aluno.
    Substitui o script procedural student.py (God Class).
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

    def run_menu(self, student_id: int) -> None:
        student = self._accounts.find_by_id(student_id)
        if student is None:
            console.print("[red]Sessão inválida.[/]")
            return

        while True:
            console.print(f"\n[green]Bem-vindo, {student.username}![/]", justify="center")
            console.print("1. [green]Verificar Disponibilidade")
            console.print("2. [green]Reservar Livro")
            console.print("3. [green]Atualizar E-mail")
            console.print("4. [green]Receber Cartão da Biblioteca")
            console.print("5. [green]Pagar Multa")
            console.print("6. [green]Sair")

            ch = input("Enter >> ").strip()

            if ch == "1":
                self._handle_check_availability()
            elif ch == "2":
                self._handle_reserve(student_id)
            elif ch == "3":
                self._handle_update_email(student_id)
            elif ch == "4":
                self._handle_library_card(student)
            elif ch == "5":
                self._handle_pay_fine(student_id)
            elif ch == "6":
                break
            else:
                console.print("[red]Opção inválida.[/]")

            # Recarrega dados do aluno para refletir mudanças
            student = self._accounts.find_by_id(student_id)

    # ──────────────────────────────────────────────────────────
    # CASOS DE USO
    # ──────────────────────────────────────────────────────────

    def check_availability(self, book_id: int) -> None:
        book = self._books.find_by_id(book_id)
        if book is None:
            console.print("[red]Livro não encontrado.[/]")
            return

        status = "[green]Disponível[/]" if book.is_available else "[red]Indisponível[/]"
        console.print(
            f"[cyan]{book.title}[/] ({book.author}) — {status}"
        )

    def reserve_book(self, book_id: int, student_id: int) -> bool:
        book = self._books.find_available(book_id)
        if book is None:
            console.print("[red]Livro não disponível para reserva.[/]")
            return False

        # Marca como reservado usando update direto no repositório
        book.reserved = student_id
        self._books.update(book)
        console.print("[green]Livro reservado com sucesso![/]")
        logger.info("Livro %s reservado pelo aluno %s", book_id, student_id)
        return True

    def update_email(self, student_id: int, new_email: str) -> bool:
        self._accounts.update_email(student_id, new_email)
        console.print("[green]E-mail atualizado com sucesso![/]")
        logger.info("E-mail atualizado para conta %s", student_id)
        return True

    def pay_fine(self, student_id: int) -> None:
        student = self._accounts.find_by_id(student_id)
        if student is None:
            return

        if student.amount <= 0:
            console.print("[green]Você não possui multas pendentes.[/]")
            return

        console.print(f"[yellow]Multa pendente: R$ {student.amount:.2f}[/]")
        # Integração com Cashfree mantida via mail service (sem alteração de lógica de pagamento)
        try:
            self._mail.send_pgto(student.email, student.username, student.amount)
        except Exception as e:
            logger.error("Erro ao processar pagamento: %s", e)
            console.print("[red]Erro ao processar pagamento. Tente novamente.[/]")

    # ──────────────────────────────────────────────────────────
    # HANDLERS DO MENU
    # ──────────────────────────────────────────────────────────

    def _handle_check_availability(self) -> None:
        try:
            book_id = int(input("ID do livro > "))
            self.check_availability(book_id)
        except ValueError:
            console.print("[red]ID inválido.[/]")

    def _handle_reserve(self, student_id: int) -> None:
        try:
            book_id = int(input("ID do livro para reservar > "))
            self.reserve_book(book_id, student_id)
        except ValueError:
            console.print("[red]ID inválido.[/]")

    def _handle_update_email(self, student_id: int) -> None:
        new_email = input("Novo e-mail > ").strip()
        if not new_email or "@" not in new_email:
            console.print("[red]E-mail inválido.[/]")
            return
        self.update_email(student_id, new_email)

    def _handle_library_card(self, student) -> None:
        try:
            from utils.utils import generate_library_card
            generate_library_card(student.username, student.email)
            console.print("[green]Cartão gerado com sucesso![/]")
        except Exception as e:
            logger.error("Erro ao gerar cartão: %s", e)
            console.print("[red]Erro ao gerar cartão.[/]")

    def _handle_pay_fine(self, student_id: int) -> None:
        self.pay_fine(student_id)
