import logging
import sys

from rich.console import Console

from config import validate_config, DB_PATH
from services.library_facade import LibraryFacade
from utils.db import DatabaseManager
from utils.login import LoginService
from repositories.account_repository import AccountRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("library.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)
console = Console()


def main() -> None:
    # Valida configurações antes de iniciar — falha rápida e mensagem clara
    try:
        validate_config()
    except EnvironmentError as e:
        console.print(f"[red]Erro de configuração:[/] {e}")
        sys.exit(1)

    facade = LibraryFacade(db_path=DB_PATH)

    # LoginService precisa do AccountRepository para autenticar alunos
    db_manager = DatabaseManager(DB_PATH)
    account_repo = AccountRepository(db_manager.connection)
    login_service = LoginService(account_repo)

    try:
        # Loop de sessão: sem os.system, sem pickle, sem arquivos de sinalização
        while True:
            user = login_service.authenticate()

            if user is None:
                console.print("[yellow]Saindo...[/]")
                break

            if user.is_admin:
                facade.run_admin()          # chamada Python direta — testável
            else:
                facade.run_student(user.id) # chamada Python direta — testável

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido pelo usuário.[/]")
    except Exception as e:
        logger.exception("Erro fatal não tratado: %s", e)
        console.print("[red]Erro inesperado. Veja library.log para detalhes.[/]")
    finally:
        facade.close()
        db_manager.close()
        logger.info("Sistema encerrado.")


if __name__ == "__main__":
    main()
