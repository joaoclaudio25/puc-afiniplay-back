# Deploy do Backend no Render

> Pré-requisitos: ter testado localmente e enviado o código para o GitHub — ver [DEPLOY.md](DEPLOY.md).

- Uma conta no [Render](https://render.com) (dá pra criar com login do GitHub)

---

## 1. Criar o banco Postgres

1. No painel do Render, **New +** → **PostgreSQL**.
2. Dê um nome (ex.: `afiniplay-db`), escolha a região mais próxima e o plano gratuito/mais barato.
3. Depois de criado, abra o banco e copie a **Internal Database URL** (não a externa — a interna é mais rápida e não passa pela internet pública, já que o Web Service vai rodar na mesma infraestrutura do Render).

---

## 2. Criar o Web Service

1. **New +** → **Web Service** → conecte o repositório `afiniplay-backend` do GitHub.
2. Configurações principais:
   - **Runtime**: Python 3 (o Render lê o `runtime.txt` automaticamente)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: deixe em branco (o Render detecta o `Procfile` → `gunicorn app:app`) ou informe explicitamente `gunicorn app:app`
3. Em **Environment Variables**, adicione:

| Variável | Valor |
|---|---|
| `SECRET_KEY` | Uma string longa e aleatória só sua (não use a do código local!) — gere uma com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | A *Internal Database URL* copiada no passo 1 |
| `FRONTEND_URL` | A URL onde o frontend vai ficar publicado — pode deixar um valor provisório agora (ex.: `http://localhost:5500`) e voltar aqui para ajustar depois de seguir o [DEPLOY_HostGator.md](DEPLOY_HostGator.md) |
| `OMDB_API_KEY` | Opcional — se não definir, usa a chave padrão já embutida no `config.py` |
| `SMTP_HOST` | `smtp.gmail.com` (se quiser e-mails de verdade) |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Seu e-mail do Gmail |
| `SMTP_PASSWORD` | A senha de app de 16 caracteres (veja o `README.md` do backend) |
| `SMTP_FROM` | O mesmo e-mail de `SMTP_USER` |

Sem as variáveis `SMTP_*`, a aplicação continua funcionando normalmente — só não envia e-mails de verdade (fica só no log do serviço, que dá pra ver na aba **Logs** do Render).

4. Clique em **Create Web Service**. O primeiro deploy leva alguns minutos. Anote a URL gerada (ex.: `https://afiniplay-backend.onrender.com`) — você vai precisar dela no [DEPLOY_HostGator.md](DEPLOY_HostGator.md).

---

## 3. Aplicar as migrações no banco de produção

Depois do primeiro deploy concluído, abra a aba **Shell** do Web Service no Render (um terminal dentro do próprio ambiente publicado) e rode:

```bash
flask db upgrade
```

Isso cria todas as tabelas (`users`, `movies`, `friends`, `movie_recommendations`) no banco novo. Repita esse comando sempre que uma nova migração for adicionada ao projeto.

Teste rápido: abra a URL do backend no navegador — deve responder `{"status": "ok", "service": "AfiniPlay API"}`. É só um health-check; a aplicação de verdade é o frontend, publicado a seguir em [DEPLOY_HostGator.md](DEPLOY_HostGator.md).

---

## 4. Domínio próprio para a API (opcional)

Só faz sentido se você quiser algo como `api.afiniplay.com.br` em vez da URL padrão `.onrender.com`. Totalmente opcional — o frontend funciona normalmente apontando direto para a URL `.onrender.com`.

1. No painel do Web Service, **Settings → Custom Domains → Add Custom Domain** → `api.afiniplay.com.br`.
2. Cadastre o CNAME que o Render indicar (`api` → a URL `.onrender.com` do Web Service) no painel de DNS de onde o domínio foi registrado (ex.: [registro.br](https://registro.br), em **Meus Domínios → afiniplay.com.br → Editar Zona/DNS**).
3. Aguarde a propagação (minutos a poucas horas). O Render emite HTTPS gratuito (Let's Encrypt) automaticamente assim que o DNS estiver correto.
4. Depois disso, atualize `frontend/static/js/config.js` para `https://api.afiniplay.com.br/api` em vez da URL `.onrender.com` — ver [DEPLOY_HostGator.md](DEPLOY_HostGator.md).

---

## Observações

- **Plano gratuito "dorme"**: o Render coloca o Web Service para dormir após um tempo sem uso, e a primeira requisição depois disso demora mais (o processo precisa subir de novo) — normal, não é bug.
- **CORS**: o backend já aceita requisições de qualquer origem (`Flask-CORS`), então não há configuração extra necessária para o frontend (em qualquer domínio) conseguir chamar a API.
- **`gunicorn` não roda no Windows** — é normal que `python app.py` continue sendo como você testa o backend localmente; o `gunicorn` só entra em ação no servidor Linux do Render.
- **Erro de conexão SSL com o banco**: costuma acontecer só se você usar a URL *externa* do Postgres em vez da *interna*. Confirme que copiou a Internal Database URL no passo 1.
- **runtime.txt** está fixado em Python 3.12 (uma versão amplamente suportada) — se quiser usar outra versão, ajuste esse arquivo, mas confirme antes que o Render já suporta a versão escolhida.
- **Esqueceu de configurar alguma variável antes de publicar?** Não tem problema: edite depois (Render faz redeploy automático a cada `git push` ou alteração de variável de ambiente).
