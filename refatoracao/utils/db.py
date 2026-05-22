import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gerencia a conexão com o banco SQLite.
    Error Hiding eliminado: exceções são específicas e logadas corretamente.
    """

    def __init__(self, db_path: str = "database.db"):
        try:
            if not Path(db_path).exists():
                raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

            self.connection = sqlite3.connect(db_path)
            logger.info("Conexão com banco estabelecida: %s", db_path)

        except FileNotFoundError as e:
            logger.critical("Arquivo do banco ausente: %s", e)
            raise

        except sqlite3.DatabaseError as e:
            logger.critical("Banco corrompido ou inacessível: %s", e)
            raise sqlite3.DatabaseError(f"Falha ao abrir banco: {e}") from e

    def close(self) -> None:
        try:
            self.connection.close()
            logger.info("Conexão com banco encerrada.")
        except sqlite3.Error as e:
            logger.error("Erro ao fechar conexão: %s", e)
