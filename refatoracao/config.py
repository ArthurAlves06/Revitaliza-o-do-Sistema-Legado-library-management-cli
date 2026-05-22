import os
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do arquivo .env

# ── Banco de dados ──────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "database.db")

# ── Regras de negócio (eram Magic Numbers hardcoded) ────────
LOAN_DAYS: int = int(os.getenv("LOAN_DAYS", "15"))
FINE_PER_DAY: float = float(os.getenv("FINE_PER_DAY", "3"))

# ── SMTP ────────────────────────────────────────────────────
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD", "")

# ── Admin (eram Magic Strings hardcoded no código) ──────────
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

# ── Cashfree ────────────────────────────────────────────────
CASHFREE_API_KEY: str = os.getenv("CASHFREE_API_KEY", "")
CASHFREE_SECRET: str = os.getenv("CASHFREE_SECRET", "")


def validate_config() -> None:
    """
    Valida que as variáveis obrigatórias estão definidas.
    Chamado no início do main.py para falha rápida e clara.
    """
    missing = []
    if not SENDER_EMAIL:
        missing.append("SENDER_EMAIL")
    if not SENDER_PASSWORD:
        missing.append("SENDER_PASSWORD")
    if not ADMIN_PASSWORD:
        missing.append("ADMIN_PASSWORD")

    if missing:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias não configuradas: {', '.join(missing)}\n"
            "Copie o arquivo .env.example para .env e preencha os valores."
        )
