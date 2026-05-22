import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD

logger = logging.getLogger(__name__)


class MailService:
    """
    Serviço de e-mail.
    Credenciais movidas para .env via config.py — sem Magic Strings hardcoded.
    Error Hiding eliminado: exceções são específicas.
    """

    def send_issue(self, to: str, book_id: int, title: str,
                   author: str, return_date: str, student_name: str) -> None:
        subject = f"Empréstimo confirmado: {title}"
        body = (
            f"Olá, {student_name}!\n\n"
            f"O livro '{title}' (ID: {book_id}) de {author} foi emitido para você.\n"
            f"Data de devolução: {return_date}.\n\n"
            f"Atenciosamente,\nBiblioteca LIPS"
        )
        self._send(to, subject, body)

    def send_ret(self, to: str, book_id: int, title: str, author: str,
                 return_date: str, student_name: str, total_fine: float, fine: float) -> None:
        subject = f"Devolução confirmada: {title}"
        body = (
            f"Olá, {student_name}!\n\n"
            f"O livro '{title}' foi devolvido em {return_date}.\n"
            f"Multa deste empréstimo: R$ {fine:.2f}\n"
            f"Multa total pendente: R$ {total_fine:.2f}\n\n"
            f"Atenciosamente,\nBiblioteca LIPS"
        )
        self._send(to, subject, body)

    def send_verif(self, to: str, otp: str) -> None:
        subject = "Código de verificação — Biblioteca LIPS"
        body = f"Seu código de verificação é: {otp}\nVálido por 10 minutos."
        self._send(to, subject, body)

    def send_pgto(self, to: str, student_name: str, amount: float) -> None:
        subject = "Pagamento de multa — Biblioteca LIPS"
        body = (
            f"Olá, {student_name}!\n\n"
            f"Acesse o link para pagar sua multa de R$ {amount:.2f}.\n"
            f"[Link do Cashfree aqui]\n\n"
            f"Atenciosamente,\nBiblioteca LIPS"
        )
        self._send(to, subject, body)

    def _send(self, to: str, subject: str, body: str) -> None:
        """Envia e-mail via SMTP. Exceções propagadas para o chamador tratar."""
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to, msg.as_string())

        logger.info("E-mail enviado para %s — assunto: %s", to, subject)
