# CensoEscolarApi

API Flask com dados do Censo Escolar 2025, persistidos em PostgreSQL (Docker).

Projeto de extração e carga dos dados (cria e popula a tabela `instituicoes`): https://github.com/PHDev10/CensoEscolarData

Vídeo de demonstração: _(link a ser adicionado)_'

## Arquitetura

O fluxo de uma requisição é **Controller → Service → Repository**:

| Camada | Pasta | Responsabilidade |
|---|---|---|
| Controller | `src/controllers/` | HTTP: lê request, chama o service, devolve JSON e status |
| Service | `src/services/` | Regras de negócio e validações; sinaliza erros com exceções de domínio |
| Repository | `src/repositories/` | Acesso ao banco (SQL parametrizado, `psycopg2`) |
| Helpers | `src/helpers/` | Configuração (`.env`), conexão/schema do banco, logger, leitura de JSON, tratamento de erros |

## Banco de dados (PostgreSQL no Docker)

A API **não recarrega o censo**: ela lê e escreve na tabela `instituicoes`, criada e populada (~120 mil escolas) pelo projeto [CensoEscolarData](https://github.com/PHDev10/CensoEscolarData). A tabela `usuarios` é criada pela própria API.

Suba o container (troque `SUA_SENHA` por uma senha de sua escolha; a porta do host é 5435):

```bash
docker run -d --name postgres20262 \
  -e POSTGRES_PASSWORD=SUA_SENHA \
  -e POSTGRES_DB=censoescolar \
  -p 5435:5432 \
  -v pgdata_censo:/var/lib/postgresql \
  postgres:18.7-alpine3.24
```

Depois carregue os dados com o CensoEscolarData, apontando para o mesmo banco.

Comandos úteis (não destrutivos): `docker ps`, `docker logs postgres20262`, `docker stop postgres20262` e `docker start postgres20262`.

### Carga inicial de plano B

Na inicialização a API cria as tabelas e índices que faltarem (`CREATE ... IF NOT EXISTS`). Se uma tabela estiver **vazia**, ela é populada a partir dos JSON de `datasets/` (em uma transação). Tabelas que já têm dados nunca são alteradas.

Se o banco estiver inacessível, **não há fallback**: a subida falha com uma mensagem clara no log. Se ele cair com a API no ar, as rotas respondem `503` com `{"erro": "Banco de dados indisponível"}`.

## Instalação

Requer Python 3.9 ou superior.

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se o `venv` falhar no Linux, instale o pacote `python3-venv` (Debian/Ubuntu).

## Variáveis de ambiente

Crie o arquivo `.env` a partir do exemplo (o `.env` não é versionado) e preencha os dados do seu banco, inclusive a senha:

```powershell
Copy-Item .env.example .env     # Windows
```

```bash
cp .env.example .env            # Linux / macOS
```

| Variável | Descrição | Padrão |
|---|---|---|
| `DB_HOST` | Host do PostgreSQL | `localhost` |
| `DB_PORT` | Porta do PostgreSQL no host | `5435` |
| `DB_NAME` | Nome do banco | `censoescolar` |
| `DB_USER` | Usuário do banco | `postgres` |
| `DB_PASSWORD` | Senha do banco | _(vazio)_ |
| `CAMINHO_JSON_INSTITUICOES` | JSON da carga inicial de instituições | `datasets/escolas_pb_matriculas_2025.json` |
| `CAMINHO_JSON_USUARIOS` | JSON da carga inicial de usuários | `datasets/usuarios.json` |
| `FLASK_DEBUG` | Modo debug do Flask (`true`/`false`) | `false` |
| `FLASK_PORT` | Porta do servidor | `5000` |
| `LIMIT_MAXIMO_PAGINA` | Maior valor aceito em `limit` | `1000` |

Se a variável não existir no `.env`, vale o padrão da tabela.

## Execução

```bash
cd src
python main.py      # no Linux, com o venv ativo, `python` também funciona
```

A API sobe em `http://127.0.0.1:5000` (ou na porta definida em `FLASK_PORT`), com o container do PostgreSQL já em execução.

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/instituicoesensino` ou `/instituicaoensino` | Lista paginada (aceita `codigo`, `page` e `limit`) |
| GET | `/instituicoesensino/<co_entidade>` | Busca por código |
| POST | `/instituicoesensino` | Cria |
| PUT | `/instituicoesensino/<co_entidade>` | Atualiza |
| DELETE | `/instituicoesensino/<co_entidade>?tipo=logico\|fisico` | Remove (padrão: lógico) |
| GET | `/usuarios` | Lista paginada (aceita `page` e `limit`) |
| GET | `/usuarios/<id>` | Busca por id |
| POST | `/usuarios` | Cria |
| PUT | `/usuarios/<id>` | Atualiza |
| DELETE | `/usuarios/<id>?tipo=logico\|fisico` | Remove (padrão: lógico) |

## Paginação e volume de dados

Com ~120 mil instituições, **toda listagem é paginada**:

- `page` (padrão `1`) e `limit` (padrão `100`, máximo `LIMIT_MAXIMO_PAGINA`, ou seja, `1000`).
- O total de registros ativos vem sempre no header `X-Total-Count`.
- Sem parâmetros, a API devolve a primeira página (100 itens).

Volume observado (API local com PostgreSQL no Docker):

| Requisição | Tempo | Tamanho |
|---|---|---|
| `GET /instituicoesensino` (padrão, 100 itens) | ~30 ms | ~32 KB |
| `GET /instituicoesensino?limit=1000` | ~40 ms | ~328 KB |
| `GET /instituicoesensino?page=120&limit=1000` | ~60 ms | ~331 KB |

Os tempos são aproximados e variam com a máquina.

## Teste

Com a API rodando, em outro terminal:

```bash
python teste.py
```

O `teste.py` faz POST, PUT e DELETE, **alterando o banco** (deixa registros com `ativo = 0`). Faça um backup antes de rodar:

```bash
docker exec postgres20262 pg_dump -U <usuario> -d <banco> -Fc -f /tmp/backup_pre_teste.dump
docker cp postgres20262:/tmp/backup_pre_teste.dump ./backup_pre_teste.dump
```
