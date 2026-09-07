# Deploy do AfiniPlay no Render (Backend + Frontend) e Domínio Próprio

> ⚠️ **Antes de seguir este guia, teste tudo localmente primeiro.** As instruções de como rodar cada parte na sua máquina estão nos READMEs de cada repositório: [README.md](README.md) (seção "Como rodar o backend") e [frontend/README.md](../frontend/README.md) (seção "Como rodar localmente") — assumindo que você clonou os dois repositórios em pastas irmãs `backend/` e `frontend/`, como usado nos comandos deste guia. Só depois de ver o app funcionando em `http://localhost:5500` conversando com `http://localhost:5000` é que vale a pena publicar na internet — assim, se algo der errado no deploy, você já sabe que não é um bug da aplicação.

O AfiniPlay é dois repositórios independentes:

- **Backend** (pasta `backend/`): API Flask + Postgres.
- **Frontend** (pasta `frontend/`): HTML/CSS/JS puro, sem build step.

Este guia publica **os dois no Render**, para você não precisar criar conta em mais de uma plataforma: o backend como **Web Service** e o frontend como **Static Site** — o Render suporta os dois tipos de serviço na mesma conta, com o mesmo fluxo de domínio customizado. Se preferir usar outra hospedagem para o frontend (Netlify, Vercel, GitHub Pages, FTP comum), o processo é equivalente — troque só a seção 5 e a parte do frontend na seção 8.

---

## 0. Pré-requisitos

- Uma conta no [GitHub](https://github.com)
- Uma conta no [Render](https://render.com) (dá pra criar com login do GitHub)
- Ter testado localmente (ver aviso no topo) ✅

---

## 1. Enviar o código para o GitHub (dois repositórios)

Crie **dois** repositórios vazios no GitHub (sem README/.gitignore — já temos os nossos): um para o backend, outro para o frontend. Podem ser privados.

```bash
# Backend
cd backend
git remote add origin https://github.com/SEU-USUARIO/afiniplay-backend.git
git branch -M main
git push -u origin main

# Frontend
cd ../frontend
git remote add origin https://github.com/SEU-USUARIO/afiniplay-frontend.git
git branch -M main
git push -u origin main
```

(troque `SEU-USUARIO/...` pelos caminhos dos repositórios que você criou)

---

## 2. Backend: criar o banco Postgres no Render

1. No painel do Render, **New +** → **PostgreSQL**.
2. Dê um nome (ex.: `afiniplay-db`), escolha a região mais próxima e o plano gratuito/mais barato.
3. Depois de criado, abra o banco e copie a **Internal Database URL** (não a externa — a interna é mais rápida e não passa pela internet pública, já que o Web Service vai rodar na mesma infraestrutura do Render).

---

## 3. Backend: criar o Web Service

1. **New +** → **Web Service** → conecte o repositório `afiniplay-backend` do GitHub.
2. Configurações principais:
   - **Runtime**: Python 3 (o Render lê o `runtime.txt` automaticamente)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: deixe em branco (o Render detecta o `Procfile` → `gunicorn app:app`) ou informe explicitamente `gunicorn app:app`
3. Em **Environment Variables**, adicione:

| Variável | Valor |
|---|---|
| `SECRET_KEY` | Uma string longa e aleatória só sua (não use a do código local!) — gere uma com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | A *Internal Database URL* copiada no passo 2 |
| `FRONTEND_URL` | A URL onde o frontend vai ficar publicado (veja o passo 5) — pode deixar um valor provisório agora e voltar aqui para ajustar depois, ex.: `https://afiniplay-frontend.onrender.com` |
| `OMDB_API_KEY` | Opcional — se não definir, usa a chave padrão já embutida no `config.py` |
| `SMTP_HOST` | `smtp.gmail.com` (se quiser e-mails de verdade) |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Seu e-mail do Gmail |
| `SMTP_PASSWORD` | A senha de app de 16 caracteres (veja o `README.md` do backend) |
| `SMTP_FROM` | O mesmo e-mail de `SMTP_USER` |

Sem as variáveis `SMTP_*`, a aplicação continua funcionando normalmente — só não envia e-mails de verdade (fica só no log do serviço, que dá pra ver na aba **Logs** do Render).

4. Clique em **Create Web Service**. O primeiro deploy leva alguns minutos. Anote a URL gerada (ex.: `https://afiniplay-backend.onrender.com`) — você vai precisar dela no passo 5.

---

## 4. Backend: aplicar as migrações no banco de produção

Depois do primeiro deploy concluído, abra a aba **Shell** do Web Service no Render (um terminal dentro do próprio ambiente publicado) e rode:

```bash
flask db upgrade
```

Isso cria todas as tabelas (`users`, `movies`, `friends`, `movie_recommendations`) no banco novo. Repita esse comando sempre que uma nova migração for adicionada ao projeto.

Teste rápido: abra a URL do backend no navegador — deve responder `{"status": "ok", "service": "AfiniPlay API"}`. É só um health-check; a aplicação de verdade é o frontend (próximo passo).

---

## 5. Frontend: publicar no Render (Static Site)

1. Antes de publicar, edite `frontend/static/js/config.js` com a URL do backend do passo 3:
   ```js
   const API_BASE_URL = "https://afiniplay-backend.onrender.com/api";
   ```
   Commite e dê `git push` nesse repositório.
2. No painel do Render: **New +** → **Static Site** → conecte o repositório `afiniplay-frontend` do GitHub.
3. Configurações:
   - **Build Command**: deixe em branco (não há build)
   - **Publish Directory**: `.` (a raiz do repositório, que já é a pasta `frontend/`)
4. Clique em **Create Static Site**. O Render te dá uma URL do tipo `https://afiniplay-frontend.onrender.com` (com HTTPS automático).
5. Acesse `https://afiniplay-frontend.onrender.com/login.html` para confirmar (a raiz `/` carrega `index.html`, que exige login).

---

## 6. Conectar os dois lados

Volte no Web Service do backend e atualize a variável `FRONTEND_URL` com a URL real do Static Site do passo 5 (sem barra no final) — isso é usado para montar os links de e-mail (redefinição de senha, convite de amigo). Salvar a variável já reinicia o serviço automaticamente.

---

## 7. Testar

Abra a URL do frontend (`.../login.html`), cadastre uma conta e teste o fluxo completo — inclusive convidar um "amigo" de verdade para validar o e-mail e conferir se o link aponta para o frontend correto.

⚠️ No plano gratuito, o Render "dorme" o **Web Service** (backend) após um tempo sem uso, e a primeira requisição depois disso demora mais (o processo precisa subir de novo) — normal, não é bug. O **Static Site** (frontend) não dorme.

---

## 8. Usar seu domínio (afiniplay.com.br)

Como os dois serviços estão no Render, o processo de domínio é o mesmo nos dois — só muda em qual painel você faz.

**Frontend → domínio raiz** (`afiniplay.com.br` e `www.afiniplay.com.br`):
1. No painel do Static Site, **Settings → Custom Domains → Add Custom Domain**.
2. O Render mostra os registros DNS necessários (tipicamente um **CNAME** para `www` e um registro **A**/**ALIAS** para o domínio raiz `@`).
3. Cadastre esses registros no painel de DNS de onde o domínio foi registrado — se foi no [registro.br](https://registro.br), em **Meus Domínios → afiniplay.com.br → Editar Zona/DNS**.
4. Aguarde a propagação (minutos a poucas horas). O Render emite HTTPS gratuito (Let's Encrypt) automaticamente assim que o DNS estiver correto.
5. Depois que o domínio estiver ativo, atualize `FRONTEND_URL` no Web Service (passo 6) para `https://afiniplay.com.br`.

**Backend → subdomínio** (opcional, ex.: `api.afiniplay.com.br`):
1. No painel do Web Service, **Settings → Custom Domains → Add Custom Domain** → `api.afiniplay.com.br`.
2. Cadastre o CNAME que o Render indicar (`api` → a URL `.onrender.com` do Web Service).
3. Depois disso, atualize `frontend/static/js/config.js` para `https://api.afiniplay.com.br/api`, commite e dê push (o Render republica sozinho).

Você **não precisa** contratar nenhum serviço de hospedagem adicional só para o DNS — o próprio registro.br já oferece esse painel de gerenciamento gratuitamente.

---

## Observações finais

- **Sem Docker em produção**: o `docker-compose.yml` continua útil só para desenvolvimento local (sobe o Postgres na sua máquina). Em produção, quem fornece o Postgres é o próprio Render.
- **CORS**: o backend já aceita requisições de qualquer origem (`Flask-CORS`), então não há configuração extra necessária para o frontend conseguir chamar a API de um domínio diferente.
- **`gunicorn` não roda no Windows** — é normal que `python app.py` continue sendo como você testa o backend localmente; o `gunicorn` só entra em ação no servidor Linux do Render.
- **Se aparecer erro de conexão SSL com o banco**: isso costuma acontecer só se você usar a URL *externa* do Postgres em vez da *interna*. Confirme que copiou a Internal Database URL no passo 2.
- **runtime.txt** (backend) está fixado em Python 3.12 (uma versão amplamente suportada) — se quiser usar outra versão, ajuste esse arquivo, mas confirme antes que o Render já suporta a versão escolhida.
- **Esqueceu de configurar `config.js` ou `FRONTEND_URL` antes de publicar?** Não tem problema: edite o arquivo/variável e publique de novo (o Render faz redeploy automático a cada `git push` ou alteração de variável de ambiente).
