import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import config

logger = logging.getLogger(__name__)

def enviar_email_confirmacao(destinatario, nome, token):
    link = config.FRONTEND_URL + "/confirmacao_conta.html?token=" + token

    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = "Confirme seu e-mail"
    mensagem["From"] = config.SMTP_REMETENTE
    mensagem["To"] = destinatario

    corpo_texto = (
        "Olá, " + nome + "!\n\n"
        "Obrigado por criar sua conta no Nba Analytics.\n\n"
        "Para ativar sua conta, acesse o link abaixo:\n"
        + link + "\n\n"
        "Se você não criou uma conta, ignore este e-mail.\n\n"
        "Equipe Nba Analytics"
    )

    corpo_html = (
        "<!DOCTYPE html>"
        "<html lang='pt-BR'><head><meta charset='UTF-8'></head><body>"
        "<div style='font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;'>"
        "<div style='font-size:1.4rem;font-weight:700;color:#F75C03;margin-bottom:8px;'>Nba Analytics</div>"
        "<h2 style='font-size:1.1rem;color:#1A1A2E;margin-bottom:16px;'>Confirme seu e-mail</h2>"
        "<p style='color:#555570;font-size:0.95rem;'>Olá, <strong>" + nome + "</strong>!</p>"
        "<p style='color:#555570;font-size:0.95rem;'>Obrigado por criar sua conta. Clique no botão abaixo para ativar o acesso à plataforma:</p>"
        "<a href='" + link + "' style='display:inline-block;margin:20px 0;padding:12px 28px;background-color:#F75C03;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;font-size:0.95rem;'>Confirmar minha conta</a>"
        "<p style='color:#888899;font-size:0.8rem;margin-top:24px;'>Se o botão não funcionar, copie e cole este link no seu navegador:</p>"
        "<p style='color:#888899;font-size:0.8rem;word-break:break-all;'>" + link + "</p>"
        "<hr style='border:none;border-top:1px solid #D0D0E0;margin:24px 0;'>"
        "<p style='color:#888899;font-size:0.75rem;'>Se você não criou uma conta no NbaAnalytics, ignore este e-mail.</p>"
        "</div></body></html>"
    )

    parte_texto = MIMEText(corpo_texto, "plain", "utf-8")
    parte_html = MIMEText(corpo_html, "html", "utf-8")
    mensagem.attach(parte_texto)
    mensagem.attach(parte_html)

    try:
        servidor = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        servidor.ehlo()
        servidor.starttls()
        servidor.login(config.SMTP_USUARIO, config.SMTP_SENHA)
        servidor.sendmail(config.SMTP_REMETENTE, destinatario, mensagem.as_string())
        servidor.quit()
        logger.info("E-mail de confirmacao enviado para %s", destinatario)
    except Exception as erro:
        logger.error("Falha ao enviar e-mail para %s: %s", destinatario, erro)
        raise erro


def enviar_email_reset_senha(destinatario, nome, token):
    link = config.FRONTEND_URL + "/redefinir_senha.html?token=" + token

    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = "Redefinir sua senha"
    mensagem["From"] = config.SMTP_REMETENTE
    mensagem["To"] = destinatario

    corpo_texto = (
        "Olá, " + nome + "!\n\n"
        "Recebemos uma solicitação para redefinir a senha da sua conta no Nba Analytics.\n\n"
        "Acesse o link abaixo para criar uma nova senha:\n"
        + link + "\n\n"
        "Este link expira em 1 hora.\n\n"
        "Se você não solicitou a redefinição, ignore este e-mail. Sua senha não será alterada.\n\n"
        "Equipe Nba Analytics"
    )

    corpo_html = (
        "<!DOCTYPE html>"
        "<html lang='pt-BR'><head><meta charset='UTF-8'></head><body>"
        "<div style='font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;'>"
        "<div style='font-size:1.4rem;font-weight:700;color:#F75C03;margin-bottom:8px;'>Nba Analytics</div>"
        "<h2 style='font-size:1.1rem;color:#1A1A2E;margin-bottom:16px;'>Redefinir senha</h2>"
        "<p style='color:#555570;font-size:0.95rem;'>Olá, <strong>" + nome + "</strong>!</p>"
        "<p style='color:#555570;font-size:0.95rem;'>Recebemos uma solicitação para redefinir a senha da sua conta. Clique no botão abaixo para criar uma nova senha:</p>"
        "<a href='" + link + "' style='display:inline-block;margin:20px 0;padding:12px 28px;background-color:#F75C03;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;font-size:0.95rem;'>Redefinir minha senha</a>"
        "<p style='color:#888899;font-size:0.8rem;margin-top:8px;'>Este link expira em <strong>1 hora</strong>.</p>"
        "<p style='color:#888899;font-size:0.8rem;margin-top:8px;'>Se o botão não funcionar, copie e cole este link no seu navegador:</p>"
        "<p style='color:#888899;font-size:0.8rem;word-break:break-all;'>" + link + "</p>"
        "<hr style='border:none;border-top:1px solid #D0D0E0;margin:24px 0;'>"
        "<p style='color:#888899;font-size:0.75rem;'>Se você não solicitou a redefinição, ignore este e-mail. Sua senha não será alterada.</p>"
        "</div></body></html>"
    )

    parte_texto = MIMEText(corpo_texto, "plain", "utf-8")
    parte_html = MIMEText(corpo_html, "html", "utf-8")
    mensagem.attach(parte_texto)
    mensagem.attach(parte_html)

    try:
        servidor = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        servidor.ehlo()
        servidor.starttls()
        servidor.login(config.SMTP_USUARIO, config.SMTP_SENHA)
        servidor.sendmail(config.SMTP_REMETENTE, destinatario, mensagem.as_string())
        servidor.quit()
        logger.info("E-mail de reset enviado para %s", destinatario)
    except Exception as erro:
        logger.error("Falha ao enviar e-mail de reset para %s: %s", destinatario, erro)
        raise erro