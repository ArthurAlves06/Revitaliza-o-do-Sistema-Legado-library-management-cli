import datetime
from unittest.mock import MagicMock, patch

import pytest

from controllers.admin_controller import AdminController
from models.book import Book


@pytest.fixture
def book_repo():
    """Repositório de livros simulado (mock) — sem banco de dados real."""
    return MagicMock()


@pytest.fixture
def account_repo():
    """Repositório de contas simulado (mock)."""
    return MagicMock()


@pytest.fixture
def mail_service():
    """Serviço de e-mail simulado (mock) — sem SMTP real."""
    return MagicMock()


@pytest.fixture
def controller(book_repo, account_repo, mail_service):
    """AdminController montado com dependências simuladas."""
    return AdminController(book_repo, account_repo, mail_service)


@pytest.fixture
def livro_disponivel():
    """Livro disponível para empréstimo."""
    return Book(id=1, title="Python Fluente", author="Luciano Ramalho", price=89.90, issued_to=0, issue_date=None, reserved=0)


@pytest.fixture
def livro_emprestado():
    """Livro já emprestado para o aluno 42."""
    return Book(
        id=2,
        title="Clean Code",
        author="Robert C. Martin",
        price=75.00,
        issued_to=42,
        issue_date=str(datetime.date.today() - datetime.timedelta(days=10)),
        reserved=0,
    )


@pytest.fixture
def livro_reservado():
    """Livro disponível mas com reserva ativa."""
    return Book(id=3, title="Design Patterns", author="GoF", price=120.00, issued_to=0, issue_date=None, reserved=1)


@pytest.fixture
def aluno():
    """Conta de aluno válida."""
    return MagicMock(id=42, username="arthur", email="arthur@email.com", amount=0.0)


class TestIssueBook:
    def test_livro_nao_encontrado_retorna_false(self, controller, book_repo):
        """Se o livro não existir ou não estiver disponível, deve retornar False."""
        book_repo.find_available.return_value = None

        resultado = controller.issue_book(book_id=99, student_id=1)

        assert resultado is False
        book_repo.issue_book.assert_not_called()

    def test_aluno_nao_encontrado_retorna_false(self, controller, book_repo, account_repo, livro_disponivel):
        """Se o aluno não existir no banco, deve retornar False."""
        book_repo.find_available.return_value = livro_disponivel
        account_repo.find_by_id.return_value = None

        resultado = controller.issue_book(book_id=1, student_id=99)

        assert resultado is False
        book_repo.issue_book.assert_not_called()

    @patch("controllers.admin_controller.check_internet", return_value=False)
    def test_emprestimo_bem_sucedido(self, _, controller, book_repo, account_repo, livro_disponivel, aluno):
        """Livro disponível + aluno existente → retorna True e persiste no banco."""
        book_repo.find_available.return_value = livro_disponivel
        account_repo.find_by_id.return_value = aluno

        resultado = controller.issue_book(book_id=1, student_id=42)

        assert resultado is True
        book_repo.issue_book.assert_called_once()

    @patch("controllers.admin_controller.check_internet", return_value=False)
    def test_emprestimo_envia_email_quando_tem_internet(
        self, mock_internet, controller, book_repo, account_repo, mail_service, livro_disponivel, aluno
    ):
        """Com internet disponível, o e-mail de confirmação deve ser enviado."""
        mock_internet.return_value = True
        book_repo.find_available.return_value = livro_disponivel
        account_repo.find_by_id.return_value = aluno

        controller.issue_book(book_id=1, student_id=42)

        mail_service.send_issue.assert_called_once()

    @patch("controllers.admin_controller.check_internet", return_value=False)
    def test_emprestimo_nao_envia_email_sem_internet(
        self, _, controller, book_repo, account_repo, mail_service, livro_disponivel, aluno
    ):
        """Sem internet, o e-mail NÃO deve ser enviado."""
        book_repo.find_available.return_value = livro_disponivel
        account_repo.find_by_id.return_value = aluno

        controller.issue_book(book_id=1, student_id=42)

        mail_service.send_issue.assert_not_called()


class TestReturnBook:
    def test_livro_nao_encontrado_retorna_false(self, controller, book_repo):
        """Devolver livro inexistente deve retornar False."""
        book_repo.find_by_id.return_value = None

        resultado = controller.return_book(book_id=99)

        assert resultado is False
        book_repo.return_book.assert_not_called()

    def test_livro_disponivel_retorna_false(self, controller, book_repo, livro_disponivel):
        """Tentar devolver livro que já está disponível deve retornar False."""
        book_repo.find_by_id.return_value = livro_disponivel

        resultado = controller.return_book(book_id=1)

        assert resultado is False
        book_repo.return_book.assert_not_called()

    @patch("controllers.admin_controller.check_internet", return_value=False)
    @patch("controllers.admin_controller.LOAN_DAYS", 7)
    @patch("controllers.admin_controller.FINE_PER_DAY", 2.0)
    def test_multa_calculada_corretamente(self, _, controller, book_repo, account_repo, livro_emprestado, aluno):
        """
        Livro emprestado há 10 dias com prazo de 7 → multa = 3 × R$2,00 = R$6,00.
        """
        book_repo.find_by_id.return_value = livro_emprestado
        account_repo.find_by_id.return_value = aluno

        resultado = controller.return_book(book_id=2)

        assert resultado is True
        args = account_repo.add_fine.call_args[0]
        assert args[0] == livro_emprestado.issued_to
        assert args[1] == pytest.approx(6.0, abs=0.01)

    @patch("controllers.admin_controller.check_internet", return_value=False)
    @patch("controllers.admin_controller.LOAN_DAYS", 14)
    @patch("controllers.admin_controller.FINE_PER_DAY", 2.0)
    def test_sem_multa_dentro_do_prazo(self, _, controller, book_repo, account_repo, aluno):
        """Livro devolvido dentro do prazo não gera multa (multa = 0)."""
        livro = Book(
            id=5,
            title="Livro Teste",
            author="Autor",
            price=50.0,
            issued_to=42,
            issue_date=str(datetime.date.today() - datetime.timedelta(days=5)),
            reserved=0,
        )
        book_repo.find_by_id.return_value = livro
        account_repo.find_by_id.return_value = aluno

        controller.return_book(book_id=5)

        args = account_repo.add_fine.call_args[0]
        assert args[1] == pytest.approx(0.0, abs=0.01)


class TestAddBook:
    def test_id_duplicado_retorna_false(self, controller, book_repo):
        """Não deve adicionar livro com ID já existente."""
        book_repo.id_exists.return_value = True

        resultado = controller.add_book(1, "Título", "Autor", 50.0)

        assert resultado is False
        book_repo.add.assert_not_called()

    def test_adiciona_livro_novo_retorna_true(self, controller, book_repo):
        """Livro com ID novo deve ser adicionado e retornar True."""
        book_repo.id_exists.return_value = False

        resultado = controller.add_book(1, "Python Fluente", "Luciano", 89.90)

        assert resultado is True
        book_repo.add.assert_called_once()

    def test_livro_adicionado_com_dados_corretos(self, controller, book_repo):
        """O objeto Book passado ao repositório deve ter os dados corretos."""
        book_repo.id_exists.return_value = False

        controller.add_book(7, "Clean Code", "Martin", 75.0)

        livro_salvo = book_repo.add.call_args[0][0]
        assert livro_salvo.id == 7
        assert livro_salvo.title == "Clean Code"
        assert livro_salvo.author == "Martin"
        assert livro_salvo.price == pytest.approx(75.0)


class TestDeleteBook:
    def test_livro_inexistente_retorna_false(self, controller, book_repo):
        """Deletar livro que não existe deve retornar False."""
        book_repo.find_by_id.return_value = None

        resultado = controller.delete_book(book_id=99)

        assert resultado is False
        book_repo.delete.assert_not_called()

    def test_livro_existente_retorna_true(self, controller, book_repo, livro_disponivel):
        """Deletar livro existente deve retornar True e chamar delete no repositório."""
        book_repo.find_by_id.return_value = livro_disponivel

        resultado = controller.delete_book(book_id=1)

        assert resultado is True
        book_repo.delete.assert_called_once_with(1)


class TestEditBook:
    def test_livro_inexistente_retorna_false(self, controller, book_repo):
        """Editar livro que não existe deve retornar False."""
        book_repo.find_by_id.return_value = None

        resultado = controller.edit_book(book_id=99, title="Novo Título")

        assert resultado is False
        book_repo.update.assert_not_called()

    def test_edicao_titulo_persistida(self, controller, book_repo, livro_disponivel):
        """Alterar título deve atualizar o atributo e chamar update no repositório."""
        book_repo.find_by_id.return_value = livro_disponivel

        resultado = controller.edit_book(book_id=1, title="Novo Título")

        assert resultado is True
        assert livro_disponivel.title == "Novo Título"
        book_repo.update.assert_called_once_with(livro_disponivel)

    def test_edicao_preco_persistida(self, controller, book_repo, livro_disponivel):
        """Alterar preço deve atualizar o atributo e chamar update no repositório."""
        book_repo.find_by_id.return_value = livro_disponivel

        controller.edit_book(book_id=1, price=199.90)

        assert livro_disponivel.price == pytest.approx(199.90)
        book_repo.update.assert_called_once()