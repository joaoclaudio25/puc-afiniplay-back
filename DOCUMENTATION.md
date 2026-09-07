# Documentação Técnica — AfiniPlay

Este documento descreve a arquitetura, o modelo de dados, os principais fluxos e as decisões técnicas do backend do AfiniPlay. Para instruções de instalação e execução, veja o [README.md](README.md).

---

## 1. Visão geral

O AfiniPlay é dividido em **dois repositórios independentes**:

- **Backend** (este repositório): API REST em Flask (`/api/...`), sem nenhuma página HTML — só JSON. Pode rodar em qualquer lugar que suporte Python (PaaS, VPS, etc.) ou em container, via `Dockerfile`/`docker-compose.yml` próprios.
- **Frontend** (repositório separado): HTML/CSS/JS puro (Bootstrap 5 via CDN, sem build step), 100% estático. Pode ser hospedado em qualquer servidor de arquivos (Netlify, GitHub Pages, FTP comum). Consome a API via `fetch`, apontando para a URL do backend configurada em `static/js/config.js`.

Essa separação é o que permite publicar cada parte onde for mais conveniente — inclusive em provedores de hospedagem "tradicionais" (só arquivos, sem suporte a Python) para o frontend, já que ele não depende de nenhum runtime no servidor.

Como as duas partes rodam em origens diferentes, o backend habilita **CORS** (`Flask-CORS`, liberado para qualquer origem) para aceitar requisições do frontend independente de onde ele esteja hospedado.

O backend segue o padrão **MVC**:

| Camada | Onde vive | Responsabilidade |
|---|---|---|
| **Model** | `models.py` | Estrutura dos dados e regras que pertencem ao próprio dado (ex.: hash de senha) |
| **Controller** | `controllers/*.py` (Blueprints do Flask) | Recebe a requisição HTTP, valida entrada básica, delega ao Service, formata a resposta |
| **Service** | `services/*.py` | Regras de negócio, consultas ao banco e integrações externas (e-mail, OMDb, tradução, WhatsApp) |
| **View** | Repositório do frontend | HTML + JavaScript vanilla que consome a API via `fetch` |

A regra prática: **um controller nunca deveria conter uma query SQLAlchemy direta nem lógica de decisão complexa** — isso é papel do service correspondente. Os controllers ficam finos, só orquestrando.

> Nem sempre foi assim: até uma versão anterior, o próprio Flask servia as páginas HTML (`templates/` + `static/`, renderizadas com Jinja2) — um projeto full-stack único. O frontend foi extraído para um repositório separado para permitir hospedar cada parte onde for mais conveniente. Links gerados pelo backend (redefinição de senha, convite de amigo) que antes apontavam para si mesmo (`request.host_url`) agora apontam para a variável de ambiente `FRONTEND_URL` (ver seção 4.2 e 4.5).

---

## 2. Modelo de dados

### `User` (tabela `users`)

| Campo | Tipo | Observação |
|---|---|---|
| `id` | Integer (PK) | |
| `full_name`, `username`, `email`, `password_hash` | String | Obrigatórios (Aba 1 do cadastro). `username` e `email` são únicos. Senha nunca é armazenada em texto puro (`werkzeug.security`). |
| `age`, `birth_date`, `city`, `country`, `gender` | Opcionais | Aba 2 do cadastro/perfil |
| `streaming_platforms` | Text (JSON serializado) | Lista de chaves (`netflix`, `max`, ...) — Aba 3 |
| `streaming_other` | String | Texto livre quando `outros` está selecionado |
| `reset_token_hash`, `reset_token_expires_at` | String / DateTime | Fluxo de "esqueci minha senha" (ver seção 4.2) |

`VALID_STREAMING_PLATFORMS` (em `models.py`) é a lista fechada de chaves aceitas — tanto no cadastro quanto na validação do backend (`user_service.parse_optional_profile_fields`).

### `Movie` (tabela `movies`)

| Campo | Tipo | Observação |
|---|---|---|
| `id`, `user_id` (FK) | | Cada filme pertence a exatamente um usuário — **não há catálogo compartilhado** |
| `title`, `year`, `rating`, `poster` | String | Vindos da OMDb (ou digitados, no caso de `title`) |
| `genre` | String | Gêneros da OMDb, separados por vírgula (ex.: "Action, Sci-Fi"). A OMDb retorna a string literal `"N/A"` quando não tem gênero — normalizado para `None` em `omdb_service.search_movie`, igual à sinopse |
| `watched` | Boolean | |
| `my_rating` | Integer (1–5) | Obrigatório no momento em que `watched` vira `true` (regra aplicada no frontend e implicitamente no fluxo; ver seção 4.3) |
| `is_favorite` | Boolean | |
| `watched_on_platform` | String | Texto livre (rótulo do streaming escolhido), opcional |
| `plot` | Text | Sinopse (da OMDb, ou digitada manualmente se a OMDb não tiver) |
| `plot_pt` | Text | Cache da tradução da sinopse (evita chamar a API de tradução de novo) |
| `comment` | Text | Comentário pessoal do usuário sobre o filme |

Duplicidade de título é bloqueada por usuário em `MovieService.create` (constraint aplicada em código, não no banco).

### `Friend` (tabela `friends`)

| Campo | Tipo | Observação |
|---|---|---|
| `id`, `owner_user_id` (FK) | | Quem cadastrou este lado da amizade — cada amizade tem **duas linhas**, uma por usuário (ver seção 4.5) |
| `name`, `email`, `phone` | | Dados de contato informados pelo dono deste lado (o lado recíproco, criado automaticamente, usa o nome cadastrado na conta) |
| `status` | String (`pending` \| `registered`) | Ver fluxo de vínculo automático recíproco (seção 4.5) |
| `invited_via_email`, `invited_via_whatsapp` | Boolean | Apenas registram *como* o convite foi enviado, não confirmam entrega. Sempre `false` no lado recíproco (ele não foi "convidado", foi vinculado automaticamente). |
| `linked_user_id` (FK, nullable) | | Preenchido quando o e-mail deste lado corresponde a uma conta real (por cadastro do amigo ou por já existir no momento do cadastro do amigo) |

Um mesmo `owner_user_id` não pode cadastrar dois amigos com o mesmo `email` (`FriendService.create`).

### `MovieRecommendation` (tabela `movie_recommendations`)

| Campo | Tipo | Observação |
|---|---|---|
| `id`, `from_user_id` (FK), `to_user_id` (FK) | | Quem indicou e quem recebeu |
| `movie_title`, `movie_year`, `movie_poster`, `movie_rating`, `movie_genre`, `movie_plot` | | **Cópia** dos dados do filme no momento da indicação |
| `created_at` | DateTime | |

**Decisão de design:** os dados do filme são duplicados (denormalizados) em vez de referenciar `Movie.id` por FK. Isso porque cada usuário tem seu próprio registro de `Movie` (não existe um filme "canônico" compartilhado) — se o filme fosse referenciado por FK e o dono o removesse do catálogo dele, a indicação já recebida pelo amigo ficaria órfã ou seria apagada em cascata, o que não faz sentido (a indicação já foi "entregue"). Copiar os dados no momento do envio resolve isso de forma simples, ao custo de não refletir edições posteriores do filme original.

---

## 3. Autenticação

* **JWT stateless** (`PyJWT`), assinado com `SECRET_KEY` (via `services/auth_service.generate_token`), expira em 24h.
* O decorador `@token_required` (`services/auth_service.py`) lê o header `Authorization: Bearer <token>`, decodifica, busca o `User` no banco e injeta como primeiro argumento da view (`current_user`). Erros retornam 401 (`token ausente`, `token inválido`, `sessão expirada`, `usuário não encontrado`).
* Não há refresh token nem logout no servidor — o "logout" é só a remoção do token do `localStorage` no navegador (`auth.js`). Isso é aceitável para o escopo do projeto, mas significa que um token vazado continua válido até expirar.

---

## 4. Fluxos principais

### 4.1 Cadastro e perfil

O cadastro é dividido em 3 etapas no frontend (`login.html` + `auth.js`), mas chega ao backend como um único POST em `/api/auth/register` com todos os campos (obrigatórios + opcionais). A validação dos campos opcionais é centralizada em `user_service.parse_optional_profile_fields`, reaproveitada tanto no registro quanto na atualização de perfil (`PUT /api/users/me`) — evita duplicar a lógica de validação de idade, data, streamings, etc.

A edição de perfil (`profile.js` + modal em `index.html`) usa a mesma estrutura de abas do cadastro, mas sem o wizard "próximo/voltar" — todas as abas ficam acessíveis livremente, já que os dados já existem.

### 4.2 "Esqueci minha senha"

1. `POST /api/auth/forgot-password` — gera um token aleatório (`secrets.token_urlsafe`), guarda **apenas o hash SHA-256** dele em `reset_token_hash` (nunca o token em texto puro) com validade de 1h, e envia por e-mail um link `{FRONTEND_URL}/reset_password.html?token=<token-em-texto-puro>` (aponta para o **frontend**, não para este backend — ver `config.py`).
2. A resposta é **sempre** a mesma mensagem genérica, exista ou não o e-mail — evita que um atacante descubra quais e-mails têm conta.
3. `POST /api/auth/reset-password` recebe o token em texto puro, calcula o hash e busca o usuário por `reset_token_hash`. Se válido e não expirado, troca a senha e **invalida o token** (`reset_token_hash = None`).
4. Um e-mail de confirmação é enviado após a troca (tanto por esse fluxo quanto pela troca de senha no perfil).

### 4.3 Avaliação obrigatória ao marcar como assistido

Regra de produto: um filme só pode ser marcado como assistido junto com uma nota de 1 a 5 estrelas. Isso é aplicado no frontend (`catalog_ui.js`): o botão "Assistido" nunca envia `watched: true` sozinho — ele abre o modal de avaliação (`ratingModal`), e só depois de escolher uma nota (1 a 5) o `PUT /api/movies/{id}` é disparado com `watched` e `my_rating` juntos. Ao desmarcar, `my_rating` e `watched_on_platform` são explicitamente zerados na mesma requisição.

O backend **não** re-valida essa regra (`MovieService.update` aceita qualquer combinação de campos) — a garantia é só do frontend. Se a API for chamada diretamente (Postman, etc.), é possível marcar como assistido sem nota. Ver seção 6 (limitações conhecidas).

### 4.4 Sinopse e tradução

* Ao adicionar um filme pela busca, a sinopse (`Plot` da OMDb) já vem preenchida. A OMDb retorna a **string literal `"N/A"`** quando não tem sinopse (comum em títulos em português) — isso é normalizado para `None` em `omdb_service.search_movie`, tanto na criação quanto na função `isPlotMissing()` do frontend (que também trata dados antigos que já tinham `"N/A"` salvo literalmente, sem precisar de migração).
* Ao abrir os detalhes de um filme sem sinopse, o frontend tenta buscar de novo na OMDb (`GET /api/search?title=...`) e salva o resultado silenciosamente (best-effort) para não repetir a busca depois.
* Se mesmo assim não houver sinopse, o botão "Traduzir" é substituído por "Adicionar Sinopse", permitindo digitar manualmente (vira o novo `plot` do filme).
* **Tradução**: `POST /api/movies/{id}/translate-plot` chama a [MyMemory Translation API](https://mymemory.translated.net/) (gratuita, sem chave) e guarda o resultado em `plot_pt`. Chamadas seguintes retornam o valor em cache sem nova chamada externa — importante porque a API gratuita tem limite de uso diário.

### 4.5 Amigos: convite e vínculo automático (recíproco)

A amizade no AfiniPlay é sempre **bidirecional**: se a conta de A aparece como amiga na lista de B, o inverso também é garantido pelo backend — cada lado é um registro `Friend` independente (um por usuário/e-mail), mas o service mantém os dois sincronizados sempre que descobre que o e-mail do outro lado corresponde a uma conta real.

1. Antes de enviar o formulário, o frontend chama `GET /api/friends/check-email?email=...` (dispara no `blur` do campo de e-mail) para saber se esse e-mail já pertence a uma conta AfiniPlay. Se pertencer, a UI esconde as opções de convite (e-mail/WhatsApp) e troca o botão para "Adicionar como Amigo" — não faz sentido convidar quem já tem conta.
2. `POST /api/friends` cria o registro do lado de quem está adicionando. O backend refaz essa mesma checagem (`FriendService.find_registered_user_by_email`) de forma independente do frontend — é ela quem decide o comportamento, não o formulário:
   - Se o e-mail informado **já pertencer a uma conta existente**: nenhum convite é enviado (mesmo que `invite_via_email`/`invite_via_whatsapp` venham `true` no payload — são ignorados nesse caso), o registro já nasce com `status = "registered"` e a amizade recíproca é criada na hora do lado da outra conta (`FriendService._ensure_registered_link`). A validação "escolha uma forma de convite" e "telefone obrigatório para WhatsApp" também não se aplica aqui.
   - Caso contrário (e-mail ainda não cadastrado), o comportamento é o de convite normal, conforme os checkboxes escolhidos:
     - **E-mail**: `email_service.send_email` envia um convite com link `{FRONTEND_URL}/login.html?tab=register` (a página de login, no repositório do frontend, lê esse parâmetro e já abre na aba de cadastro — `auth.js`).
     - **WhatsApp**: `whatsapp_service.build_whatsapp_link` monta um link `https://wa.me/<telefone>?text=<mensagem>` (assume Brasil — prefixa `55` se o telefone tiver 10 ou 11 dígitos) e devolve na resposta; **o frontend é quem abre o link** (`window.open`). A API nunca envia a mensagem sozinha — não há integração com a API oficial do WhatsApp Business (ver seção 6).
3. Quando **qualquer pessoa** se registra (`POST /api/auth/register`), `FriendService.link_registered_friends_to_new_user` procura, em toda a base, registros de `Friend` com `status = "pending"` e o mesmo e-mail do novo usuário (não importa quem convidou). Para cada um encontrado: marca `status = "registered"`, preenche `linked_user_id`, **cria (ou atualiza) o registro recíproco do lado do novo usuário** — ele já começa o uso enxergando quem o convidou como amigo, sem precisar cadastrar ninguém manualmente — e envia um e-mail ao dono do convite avisando que o amigo aceitou.
4. Isso significa que o vínculo (nos dois sentidos) funciona mesmo que a pessoa se cadastre **sem nunca ter clicado no link do convite** — basta usar o mesmo e-mail.

### 4.6 Indicação de filmes entre amigos

1. O botão de indicar (📤) só aparece em filmes com `watched = true`.
2. O modal lista apenas amigos do usuário atual com `status = "registered"` (`GET /api/friends`, filtrado no frontend).
3. `POST /api/recommendations` valida no backend: o filme pertence ao usuário autenticado, está marcado como assistido, e cada `friend_id` enviado corresponde a um amigo do usuário com `status = "registered"` (`FriendService.get_registered_by_ids`) — ids inválidos ou de amigos ainda pendentes são silenciosamente ignorados (só falha se **nenhum** for válido).
4. Uma `MovieRecommendation` é criada por destinatário (`RecommendationService.create_many`), copiando os dados do filme (ver seção 2).
5. Quem recebeu vê a seção "Filmes Indicados para Você" (`friends_ui.js`, carregada no `DOMContentLoaded` de `index.html`) e pode:
   - **Dispensar** (`DELETE /api/recommendations/{id}`) — só remove a indicação.
   - **Adicionar ao catálogo** (`POST /api/recommendations/{id}/add-to-catalog`) — cria um novo `Movie` no catálogo de quem recebeu, usando os dados copiados na indicação (não assistido, sem nota própria), e remove a indicação da lista de pendentes. Se o destinatário já tiver um filme com o mesmo título, `MovieService.create` retorna `"duplicate"` — nesse caso o filme não é duplicado, mas a indicação é removida do mesmo jeito (a resposta muda para avisar que o filme já estava no catálogo).

---

## 5. Decisões técnicas e justificativas

* **Alembic/Flask-Migrate em vez de `db.create_all()`**: `create_all()` só cria tabelas que não existem — nunca altera colunas de tabelas já existentes. Em um projeto com dados reais, isso já causou um incidente (login quebrado após adicionar colunas ao `User` sem migração). Toda mudança de schema agora passa por `flask db migrate` + `flask db upgrade`.
* **JWT em vez de sessão no servidor**: simplicidade (sem necessidade de Redis/store de sessão), adequado ao escopo do projeto. Trade-off: sem revogação de token antes da expiração.
* **Tokens de reset armazenados como hash**: mesmo princípio de senhas — se o banco vazar, os tokens de redefinição não podem ser reutilizados diretamente.
* **`.env` + `python-dotenv`** para segredos (SMTP): evita hardcodar credenciais no código (diferente da chave da OMDb, que é pública/gratuita e foi mantida no `config.py` deliberadamente — ver README).
* **WhatsApp via link `wa.me` em vez da API oficial do WhatsApp Business**: a API oficial exige conta Meta Business verificada, número de telefone comercial e geralmente tem custo por mensagem — desproporcional para o escopo atual. O link `wa.me` funciona imediatamente, de graça, mas exige uma ação manual do usuário (tocar em "enviar").
* **Tradução via MyMemory (gratuita) em vez da Google Cloud Translation API**: a API do Google exige projeto no Google Cloud com faturamento habilitado. MyMemory tem limite de uso mais restrito, mas não exige nenhuma configuração — resultado em cache no próprio filme (`plot_pt`) minimiza o número de chamadas.
* **Dados da indicação denormalizados** (`MovieRecommendation`): ver justificativa na seção 2.
* **Amizade como duas linhas em vez de uma relação N:N com tabela de associação única**: cada lado (`Friend`) guarda seus próprios `name`/`phone` — a mesma pessoa pode estar salva com nomes diferentes em cada agenda (ex.: "Zé" para um amigo, "José Silva" para outro), o que uma única linha compartilhada não permitiria. O custo é ter que manter os dois lados sincronizados manualmente no código (`FriendService._ensure_registered_link`) em vez de o banco garantir isso via constraint.
* **Um `Dockerfile`/`docker-compose.yml` por repositório, sem nenhum arquivo Docker compartilhado**: o backend sobe a API + Postgres (`docker compose up -d --build` dentro de `backend/`); o frontend sobe só o nginx servindo os arquivos estáticos (mesmo comando dentro de `frontend/`). Os dois não se conhecem no nível de infraestrutura — a única ligação é o navegador chamando `http://localhost:5000/api` a partir do `config.js` do frontend. Isso espelha de propósito o modelo de deploy real (Web Service + Static Site no Render, sem dependência de infraestrutura entre eles) já dentro do ambiente local de testes.

---

## 6. Limitações conhecidas

* A regra "nota obrigatória ao marcar como assistido" só é aplicada no frontend — a API aceita `watched: true` sem `my_rating` se chamada diretamente.
* Convite por WhatsApp não confirma envio nem entrega — é só um link pronto; se o usuário fechar a aba sem tocar em "enviar", o convite marcado como `invited_via_whatsapp = true` nunca chega de fato.
* Sem revogação de JWT: um token continua válido até expirar (24h), mesmo após logout ou troca de senha.
* `flask run` / `python app.py` usa o servidor de desenvolvimento do Werkzeug (`debug=True`) — não é adequado para produção (ver aviso do próprio Flask no console).
* MyMemory Translation tem limite de uso diário por IP para uso anônimo; em volume alto, pode começar a falhar (a função retorna erro tratado, sem quebrar a aplicação).
* CORS está liberado para **qualquer origem** (`Flask-CORS` sem restrição) — adequado para desenvolvimento e testes com amigos, mas o ideal em produção seria restringir a origem exatamente ao domínio do frontend publicado.

---

## 7. Estrutura de pastas (referência rápida)

Localmente, os dois repositórios convivem lado a lado na mesma pasta de trabalho (é assim que este projeto foi desenvolvido) — mas cada um já é, de fato, um repositório Git independente no GitHub, incluindo seu próprio Dockerfile/docker-compose.yml (ver decisão técnica na seção 5).

```
AfiniPlay/
├── venv/                      # Ambiente virtual Python (só para rodar o backend sem Docker)
├── DEPLOY.md                  # Cópia local do guia de deploy (idêntica à de cada repositório)
│
├── backend/                   # Repositório Git independente: "afiniplay-backend"
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   ├── afiniPlay.yaml         # Especificação OpenAPI/Swagger
│   ├── README.md
│   ├── DOCUMENTATION.md       # Este arquivo
│   ├── DEPLOY.md
│   ├── Dockerfile
│   ├── docker-compose.yml     # Sobe backend + Postgres, sem depender do frontend
│   ├── entrypoint.sh          # Aplica as migrações e inicia o gunicorn
│   ├── .env.example
│   ├── controllers/
│   ├── services/
│   └── migrations/
│
└── frontend/                  # Repositório Git independente: "afiniplay-frontend"
    ├── index.html
    ├── login.html
    ├── reset_password.html
    ├── README.md
    ├── DEPLOY.md
    ├── Dockerfile
    ├── docker-compose.yml     # Sobe só o container do frontend (nginx)
    └── static/
        ├── css/
        ├── img/
        └── js/
            └── config.js       # Único arquivo com a URL do backend
```
