# AfiniPlay — Rodar Localmente e Publicar na Internet

O AfiniPlay é dois repositórios independentes:

- **Backend** (pasta `backend/`): API Flask + Postgres.
- **Frontend** (pasta `frontend/`): HTML/CSS/JS puro, sem build step.

Este arquivo cobre **como rodar tudo na sua máquina** antes de publicar. Uma vez validado localmente, a publicação de cada lado tem seu próprio guia:

- **[DEPLOY_Render.md](DEPLOY_Render.md)** — publicar o backend no Render.
- **[DEPLOY_HostGator.md](DEPLOY_HostGator.md)** — publicar o frontend via FTP numa hospedagem tradicional (ex.: HostGator).

> ⚠️ **Sempre teste localmente antes de publicar.** Assim, se algo der errado no deploy, você já sabe que não é um bug da aplicação.

---

## 0. Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e rodando (opção recomendada — veja abaixo alternativa sem Docker)
- Uma conta no [GitHub](https://github.com)

---

## 1. 🐳 Rodando localmente com Docker (recomendado)

Cada repositório tem seu **próprio** `docker-compose.yml` — não existe nenhum arquivo Docker compartilhado entre os dois. Suba cada lado a partir da sua própria pasta, em qualquer ordem:

```bash
cd backend
docker compose up -d --build
```

```bash
cd frontend
docker compose up -d --build
```

O `backend/docker-compose.yml` sobe 2 containers (API Flask + Postgres), aplicando as migrações (`flask db upgrade`) automaticamente antes de iniciar. O `frontend/docker-compose.yml` sobe 1 container (nginx servindo os arquivos estáticos). Acesse **http://localhost:5500/login.html**.

Comandos úteis (rode dentro da pasta correspondente):
```bash
docker compose logs -f backend   # dentro de backend/ — acompanhar os logs da API
docker compose down              # derruba os containers daquele lado
docker compose down -v           # (só em backend/) também apaga os dados do banco
```

⚠️ O frontend não sabe nada sobre o backend no nível do Docker — a ligação entre os dois acontece só no navegador, via `frontend/static/js/config.js` apontando para `http://localhost:5000/api`. Isso é proposital: cada lado pode ser construído, testado e publicado de forma 100% independente — exatamente como vai acontecer quando publicados (Render + HostGator, sem nenhuma dependência de infraestrutura entre eles).

### Rodando sem Docker

Cada repositório também roda direto com Python/servidor de arquivos, sem Docker — veja "Como rodar o backend" em [README.md](README.md) e "Como rodar localmente" em [frontend/README.md](../frontend/README.md) (seção "Opção 2") — assumindo que você clonou os dois repositórios em pastas irmãs `backend/` e `frontend/`.

---

## 2. Enviar o código para o GitHub (dois repositórios)

Cada guia de deploy (Render, HostGator) parte do código já estar no GitHub. Crie **dois** repositórios vazios no GitHub (sem README/.gitignore — já temos os nossos): um para o backend, outro para o frontend. Podem ser privados.

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

## 3. Publicar na internet

Com os dois testados localmente e no GitHub, siga cada guia (em qualquer ordem, mas o frontend precisa saber a URL final do backend antes do seu último passo):

1. **[DEPLOY_Render.md](DEPLOY_Render.md)** — cria o Postgres, o Web Service do backend, aplica as migrações e (opcional) configura um subdomínio próprio para a API.
2. **[DEPLOY_HostGator.md](DEPLOY_HostGator.md)** — aponta o frontend para a URL do backend publicado no passo 1, envia os arquivos por FTP, e (opcional) aponta seu domínio `afiniplay.com.br` para lá.

Depois dos dois publicados, volte no Render e atualize a variável `FRONTEND_URL` do backend com a URL final do frontend (isso é usado para montar os links de e-mail — redefinição de senha, convite de amigo). Esse passo está detalhado no fim do `DEPLOY_HostGator.md`.
