import logging

from controllers.admin_controller import AdminController
from controllers.student_controller import StudentController
from repositories.book_repository import BookRepository
from repositories.account_repository import AccountRepository
from utils.db import DatabaseManager
from utils.mail import MailService

logger = logging.getLogger(__name__)


class LibraryFacade:
    """
    Facade (GoF Structural) — interface única para todos os subsistemas.
    Substitui os.system('python admin.py') + data.pickle por chamadas Python diretas.
    Elimina o Inappropriate Intimacy via sistema de arquivos.
    """

    def __init__(self, db_path: str = "database.db"):
        self._db = DatabaseManager(db_path)
        conn = self._db.connection

        book_repo = BookRepository(conn)
        account_repo = AccountRepository(conn)
        mail_service = MailService()

        self._admin = AdminController(book_repo, account_repo, mail_service)
        self._student = StudentController(book_repo, account_repo, mail_service)

    def run_admin(self) -> None:
        """Executa o menu do administrador — sem os.system."""
        self._admin.run_menu()

    def run_student(self, student_id: int) -> None:
        """Executa o menu do aluno — sem os.system."""
        self._student.run_menu(student_id)

    def close(self) -> None:
        self._db.close()
