# backend/services/email_service.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BRAND_GRADIENT = "linear-gradient(135deg, #8A23D2 0%, #E91E63 50%, #FF6B35 100%)"


def send_email(to_email, subject, html_body, text_body=None):
    """Envia um e-mail via SMTP. Se as credenciais SMTP não estiverem configuradas
    (variáveis de ambiente SMTP_HOST/SMTP_USER/SMTP_PASSWORD), apenas loga o
    conteúdo no console (modo de desenvolvimento) e não levanta exceção."""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("SMTP_FROM", smtp_user or "no-reply@afiniplay.local")

    if not smtp_host or not smtp_user or not smtp_password:
        print(
            f"[EMAIL - MODO DEV, SMTP NÃO CONFIGURADO]\n"
            f"Para: {to_email}\nAssunto: {subject}\n\n{text_body or html_body}\n",
            flush=True,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
    return True


def _email_shell(title, body_html):
    return f"""
    <div style="font-family: Arial, sans-serif; background-color: #0d0d0d; padding: 32px 0;">
      <div style="max-width: 480px; margin: 0 auto; background-color: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #333;">
        <div style="background: {BRAND_GRADIENT}; padding: 20px 24px;">
          <span style="color: #fff; font-size: 20px; font-weight: bold;">AfiniPlay</span>
        </div>
        <div style="padding: 24px; color: #eee;">
          <h2 style="color: #fff; margin-top: 0;">{title}</h2>
          {body_html}
        </div>
        <div style="padding: 16px 24px; color: #777; font-size: 12px; border-top: 1px solid #333;">
          Você recebeu este e-mail porque possui uma conta no AfiniPlay.
        </div>
      </div>
    </div>
    """


def build_password_reset_email_html(display_name, reset_link):
    body = f"""
      <p>Olá, {display_name}!</p>
      <p>Recebemos uma solicitação para redefinir a senha da sua conta. Clique no botão abaixo para criar uma nova senha:</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{reset_link}" style="background: {BRAND_GRADIENT}; color: #fff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: bold; display: inline-block;">Redefinir Senha</a>
      </p>
      <p style="color: #aaa; font-size: 13px;">Este link expira em 1 hora. Se você não solicitou essa alteração, pode ignorar este e-mail com segurança.</p>
    """
    return _email_shell("Redefinição de Senha", body)


def build_password_changed_email_html(display_name):
    body = f"""
      <p>Olá, {display_name}!</p>
      <p>Confirmamos que a senha da sua conta AfiniPlay foi alterada com sucesso.</p>
      <p style="color: #aaa; font-size: 13px;">Se você não fez essa alteração, entre em contato ou redefina sua senha imediatamente pelo link "Esqueci minha senha" na tela de login.</p>
    """
    return _email_shell("Senha Alterada", body)


def build_friend_invite_email_html(friend_name, inviter_name, register_link):
    body = f"""
      <p>Olá, {friend_name}!</p>
      <p><strong>{inviter_name}</strong> te convidou para conhecer o AfiniPlay, um app para organizar os filmes que você assiste, avaliar com estrelas e trocar indicações com amigos.</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{register_link}" style="background: {BRAND_GRADIENT}; color: #fff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: bold; display: inline-block;">Criar minha conta</a>
      </p>
      <p style="color: #aaa; font-size: 13px;">Assim que você se cadastrar, {inviter_name} vai poder te indicar filmes direto pelo app.</p>
    """
    return _email_shell("Você foi convidado!", body)


def build_friend_registered_email_html(owner_name, friend_name):
    body = f"""
      <p>Olá, {owner_name}!</p>
      <p>Boas notícias: <strong>{friend_name}</strong> aceitou seu convite e criou uma conta no AfiniPlay!</p>
      <p style="color: #aaa; font-size: 13px;">Agora você já pode indicar filmes assistidos diretamente para {friend_name} pelo app.</p>
    """
    return _email_shell("Seu amigo se cadastrou!", body)
