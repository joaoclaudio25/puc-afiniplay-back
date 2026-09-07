# AfiniPlay — Backend (API) 🎬
## README 📘

Este repositório contém **só a API** do AfiniPlay: catálogo de filmes pessoal com avaliação por estrelas, favoritos, sinopse (com tradução), comentários, cadastro de amigos com convite por e-mail/WhatsApp e indicação de filmes assistidos entre amigos.

O frontend (HTML/CSS/JS) vive em um **repositório separado** — veja [afiniplay-frontend](../frontend/README.md) (ou o link do repositório correspondente, se você já o publicou separadamente no GitHub). Este backend não serve nenhuma página HTML; ele é uma API JSON pura, com CORS habilitado para ser consumida por um frontend hospedado em qualquer lugar.

## Funcionalidades

**Conta**
* Cadastro em 3 etapas: Conta (obrigatório), Perfil Pessoal e Meus Streamings (opcionais)
* Login com JWT, "Esqueci minha senha" com link por e-mail (expira em 1h)
* Edição de perfil (mesmas 3 etapas do cadastro), com confirmação ao trocar de senha

**Catálogo de filmes**
* Busca de filmes na OMDb e adição ao catálogo pessoal (título, ano, nota IMDb, gênero e pôster)
* Filtro por assistidos/não assistidos, por favoritos e por gênero, ordenação por título ou nota
* Marcar como assistido exige avaliação de 1 a 5 estrelas (exibida sobre o pôster) e permite indicar em qual streaming foi assistido
* Favoritar filmes (❤ sobre o pôster)
* Sinopse (buscada automaticamente se estiver ausente), tradução para português, campo para escrever a sinopse manualmente quando a OMDb não tem, e comentário pessoal

**Amigos e indicações**
* Cadastro de amigos (nome, e-mail, telefone) com convite por e-mail e/ou link de WhatsApp
* Se o e-mail informado já pertencer a uma conta AfiniPlay, o convite é substituído por uma adição direta (sem convite) — a amizade já nasce confirmada nos dois sentidos
* Status do amigo (Pendente/Cadastrado) atualizado automaticamente quando ele cria uma conta com o mesmo e-mail — a amizade já nasce nos dois sentidos (quem aceitou o convite já vê quem o convidou como amigo, sem precisar cadastrar ninguém) e o convidante é notificado por e-mail
* Filmes já assistidos podem ser indicados para amigos cadastrados
* Quem recebe uma indicação pode dispensá-la ou adicionar o filme direto ao próprio catálogo

### 🧠 Regras de negócio
* Marcar um filme como assistido exige avaliação de 1 a 5 estrelas; desmarcar remove a avaliação e o streaming
* Só é possível indicar filmes já assistidos, e apenas para amigos com cadastro concluído
* Backend impede adicionar filmes duplicados (mesmo título) no mesmo catálogo
* Backend impede cadastrar dois amigos com o mesmo e-mail para o mesmo usuário

## Arquitetura 🏗️

Organizado como **MVC**:

```
backend/
├── app.py                 # Cria a app Flask, registra os Blueprints e a rota de health-check ("/")
├── config.py               # Configuração (SECRET_KEY, banco, FRONTEND_URL, chave da OMDb)
├── database.py              # Instância do SQLAlchemy
├── models.py                # Models: User, Movie, Friend, MovieRecommendation
├── controllers/              # Controllers (Blueprints) — request/response HTTP
│   ├── auth_controller.py      # Cadastro, login, esqueci/redefinir senha
│   ├── user_controller.py      # Perfil do usuário autenticado
│   ├── movie_controller.py     # CRUD de filmes + tradução de sinopse
│   ├── search_controller.py    # Busca na OMDb
│   ├── friend_controller.py    # Cadastro e convite de amigos
│   └── recommendation_controller.py  # Indicação de filmes entre amigos
├── services/                # Services — regras de negócio e integrações externas
│   ├── auth_service.py         # JWT (gerar/validar), tokens de redefinição de senha
│   ├── user_service.py         # Validação dos campos de perfil
│   ├── movie_service.py        # Regras de CRUD de filmes
│   ├── friend_service.py       # Regras de amigos e vínculo automático (recíproco) no registro
│   ├── recommendation_service.py  # Regras de indicação de filmes
│   ├── omdb_service.py         # Integração com a OMDb + tradução (MyMemory)
│   ├── whatsapp_service.py     # Geração de link de convite via WhatsApp (wa.me)
│   └── email_service.py        # Envio de e-mail (SMTP) e templates
└── migrations/                # Histórico de migrações do banco (Alembic)
```

Uma explicação mais detalhada de cada camada, dos modelos de dados e dos principais fluxos está em **[DOCUMENTATION.md](DOCUMENTATION.md)**.

## Tecnologias Utilizadas

Python, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-CORS, PyJWT, python-dotenv, PostgreSQL, gunicorn (produção)

**Integrações externas:** [OMDb API](http://www.omdbapi.com/) (busca de filmes), [MyMemory Translation](https://mymemory.translated.net/) (tradução de sinopse, gratuita), SMTP (envio de e-mail), WhatsApp via link `wa.me` (convite)

## ⚙️ Como rodar o backend

```bash
# 1. Criar e ativar o ambiente virtual (na raiz do projeto)
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash) — no PowerShell: venv\Scripts\Activate.ps1

# 2. Instalar as dependências
cd backend
pip install -r requirements.txt

# 3. Subir o banco Postgres (na raiz do projeto, onde está o docker-compose.yml)
cd ..
docker-compose up -d

# 4. Configurar variáveis de ambiente
cd backend
cp .env.example .env
# Edite o .env: pelo menos FRONTEND_URL (onde o frontend está rodando — veja abaixo)
# e, se quiser e-mails de verdade, as credenciais SMTP (veja a seção mais abaixo).

# 5. Aplicar as migrações do banco
export FLASK_APP=app.py   # no PowerShell: $env:FLASK_APP = "app.py"
flask db upgrade

# 6. Rodar a aplicação
python app.py
```

A API sobe em **http://localhost:5000** — acessar essa URL direto no navegador só mostra um health-check (`{"status": "ok"}`), já que não há páginas aqui. Você vai usar o **frontend** (repositório separado) para de fato navegar na aplicação.

### Rodando o frontend junto (desenvolvimento local)

O frontend é 100% arquivos estáticos — não precisa de Python/Node para rodar, qualquer servidor de arquivos estáticos serve:

```bash
cd frontend
python -m http.server 5500
```

Acesse **http://localhost:5500/login.html**. Confira que `frontend/static/js/config.js` aponta `API_BASE_URL` para `http://localhost:5000/api` (valor padrão já configurado) e que o `.env` do backend tem `FRONTEND_URL=http://localhost:5500` — essas duas pontas precisam concordar uma com a outra.

📌 CORS já está liberado (`Flask-CORS`) para qualquer origem, então o frontend pode rodar em qualquer porta/domínio sem configuração adicional no backend.

## 🚀 Deploy (colocar no ar para testar com amigos)

Para publicar backend e frontend em serviços de hospedagem separados, com domínio próprio, veja o passo a passo completo em **[DEPLOY.md](DEPLOY.md)**.

## 📄 Documentação da API (Swagger / OpenAPI)

O contrato completo da API está em [`afiniPlay.yaml`](afiniPlay.yaml) (OpenAPI 3.0). Para visualizar de forma interativa:

* **Online:** cole o conteúdo do arquivo no [Swagger Editor](https://editor.swagger.io/)
* **Localmente:** `pip install openapi-spec-validator` para apenas validar, ou use uma extensão de Swagger/OpenAPI Preview no VS Code para visualizar

## 🗄️ Migrações de Banco de Dados (Alembic / Flask-Migrate)

O schema do banco é gerenciado pelo Alembic via Flask-Migrate — o SQLAlchemy `db.create_all()` **não** altera tabelas já existentes, então qualquer mudança nos models (`models.py`) precisa de uma migração para não quebrar bancos com dados reais.

Sempre que alterar `models.py` (adicionar/remover/mudar uma coluna, etc.):

```bash
# 1. Suba o banco (se ainda não estiver rodando)
docker-compose up -d

# 2. Gere a migração comparando os models com o banco atual
cd backend
export FLASK_APP=app.py        # no PowerShell: $env:FLASK_APP = "app.py"
flask db migrate -m "descreva a mudança aqui"

# 3. Revise o arquivo gerado em backend/migrations/versions/
#    (o autogenerate nem sempre acerta 100%, principalmente em SQLite)

# 4. Aplique a migração no banco
flask db upgrade
```

Outros comandos úteis:
- `flask db current` — mostra a revisão aplicada no banco atual.
- `flask db history` — lista todas as migrações.
- `flask db downgrade -1` — desfaz a última migração.

⚠️ Nunca edite colunas diretamente no banco fora desse fluxo — isso desalinha o histórico do Alembic com o schema real.

## 📧 Envio de E-mail (Redefinição de Senha e Convites de Amigos)

A aplicação envia e-mails em três momentos: "Esqueci minha senha", confirmação de troca de senha, e convite de amigo (além de notificar quando um amigo convidado se cadastra). O envio é feito via SMTP e configurado por variáveis de ambiente. Os links dentro desses e-mails (redefinir senha, aceitar convite) sempre apontam para `FRONTEND_URL`, não para este backend.

**Sem configuração:** o e-mail não é enviado de verdade — o conteúdo (incluindo o link) é apenas impresso no console do servidor. Bom para testar localmente sem precisar de credenciais reais.

**Para enviar de verdade com Gmail:**

1. Ative a verificação em duas etapas na sua Conta Google.
2. Gere uma "Senha de app" em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (não é a sua senha normal do Gmail).
3. No `backend/.env`, preencha:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=seu-email@gmail.com
   SMTP_PASSWORD=sua-senha-de-app-de-16-caracteres
   SMTP_FROM=seu-email@gmail.com
   ```
4. O `.env` é carregado automaticamente ao iniciar a aplicação (`python app.py` ou `flask ...`) e nunca deve ser commitado — já está no `.gitignore`.

Usando outro provedor SMTP (SendGrid, Mailgun, Amazon SES, etc.), basta apontar `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD` para as credenciais correspondentes.

**Convite por WhatsApp:** não envia nada automaticamente — a API gera um link `wa.me` com a mensagem pronta, e o navegador do usuário que convida é quem abre o WhatsApp para ele mesmo tocar em enviar. Não requer nenhuma credencial.

## Observações
A solução usa uma API pública (OMDb) e no código estamos utilizando a API_KEY do autor. Não quis encapsular isso, pois exigiria que o professor criasse uma API_KEY para utilizar a solução.
