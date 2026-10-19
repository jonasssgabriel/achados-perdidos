# Relatório técnico: Achados & Perdidos

Este relatório explica o ambiente entregue: o `app/Dockerfile`, o `docker-compose.yml`, o caminho de uma requisição `POST /itens` com foto e o ciclo de vida dos volumes. Todos os resultados citados vêm de [`docs/evidencias/`](evidencias/), gerados neste ambiente.

---

## (a) O Dockerfile, instrução por instrução

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/uploads \
    && useradd --system --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

| # | Instrução | O que faz | Por que está nesta posição |
|---|---|---|---|
| 1 | `FROM python:3.12-slim` | Parte da imagem oficial do Python 3.12, na variante `slim` | É a base de tudo. `slim` é uma versão enxuta do Debian: menor e com menos programas, logo menos superfície de ataque. Nada de instalar Python à mão (RNF01) |
| 2 | `WORKDIR /app` | Define `/app` como pasta de trabalho (criada se não existir) | Os comandos seguintes rodam ali; `/app/uploads` é o caminho em que o `app.py` grava fotos |
| 3 | `COPY requirements.txt .` | Copia só a lista de dependências | Vem **antes** do código de propósito (ver abaixo) |
| 4 | `RUN pip install --no-cache-dir -r requirements.txt` | Instala Flask, psycopg e Gunicorn; `--no-cache-dir` evita guardar o cache do pip na imagem | Camada cara (cerca de 7 s no primeiro build); fica em cache enquanto o `requirements.txt` não mudar |
| 5 | `COPY . .` | Copia o restante do código (`app.py`) | Vem **depois** das dependências: o código muda com frequência, as dependências não |
| 6 | `RUN mkdir -p /app/uploads && useradd ... && chown -R ...` | Cria a pasta de uploads, cria o usuário `appuser` sem login e o torna dono de `/app` | Tem que vir depois do `COPY . .`, para o `chown` alcançar os arquivos copiados. Sem o dono certo, o `appuser` não conseguiria gravar fotos |
| 7 | `USER appuser` | Tudo que vem depois (inclusive o processo do contêiner) roda como `appuser` | Atende ao RNF04. Se a aplicação for invadida, o invasor não é `root` no contêiner. `docker compose exec web whoami` retorna `appuser` ([evidência 12](evidencias/12-whoami.txt)) |
| 8 | `EXPOSE 5000` | Documenta que a aplicação usa a porta 5000 | É só documentação: **não publica** a porta. Quem publica é o `ports:` do Compose |
| 9 | `CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]` | Inicia o Gunicorn | Ver abaixo |

**Ordem das instruções e cache (Q5).** O Docker guarda cada instrução como uma camada e a reaproveita se a instrução e tudo que ela depende não mudaram. Se o `COPY . .` viesse antes do `pip install`, qualquer alteração no `app.py` invalidaria essa camada e todas as seguintes, e o pip rodaria de novo. Com `requirements.txt` copiado primeiro, alterar só o `app.py` refaz apenas as camadas 5 em diante. O segundo build deste projeto mostrou `CACHED` nas camadas 2 a 6, e levou 0,5 s.

**Detalhes do `CMD`:**
- `0.0.0.0` faz o Gunicorn escutar em todas as interfaces do contêiner. Com `127.0.0.1`, só o próprio contêiner o alcançaria e a porta publicada não responderia.
- `app:app` significa "módulo `app.py`, objeto `app`".
- A **forma exec** (lista com colchetes) executa o Gunicorn diretamente como processo principal (PID 1), que recebe os sinais do `docker stop` e encerra com limpeza. Na forma *shell*, o PID 1 seria um `sh` que não repassa os sinais.
- O Gunicorn é o servidor de produção; o servidor embutido do Flask é só para desenvolvimento.

**`.dockerignore`.** Contém `.env`, `__pycache__/` e `*.pyc`. Ele controla o *contexto de build* (o que o Docker recebe para construir). Sem ele, o `.env` poderia ser copiado para dentro da imagem pelo `COPY . .`, deixando a senha dentro dela (violaria o RNF03).

---

## (b) O `docker-compose.yml`, bloco por bloco

### Serviço `db`

| Propriedade | Função |
|---|---|
| `image: postgres:16-alpine` | Imagem oficial pronta (não precisa de Dockerfile próprio). `alpine` é a variante enxuta |
| `environment: POSTGRES_DB / USER / PASSWORD` | A imagem lê essas variáveis na **primeira** inicialização para criar o banco, o usuário e a senha. Os valores vêm do `.env`, via `${...}` |
| `volumes: dados_banco:/var/lib/postgresql/data` | **Volume nomeado** com o diretório de dados do PostgreSQL. É o que faz o banco sobreviver à recriação do contêiner |
| `volumes: ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro` | **Bind mount** do arquivo do projeto. A imagem executa os `.sql` dessa pasta **somente se o diretório de dados estiver vazio**. `:ro` torna a montagem somente leitura |
| `healthcheck` | Executa `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` a cada 5 s (timeout 5 s, até 10 tentativas). O serviço só vira `healthy` quando o PostgreSQL aceita conexões |
| `networks: rede_interna` | Conecta o serviço à rede privada |
| `restart: unless-stopped` | Religa o contêiner se ele cair ou o Docker reiniciar, exceto se eu o parei manualmente |
| *(sem `ports:`)* | O banco **não é publicado** no host. A 5432 existe só dentro da rede ([evidência 13](evidencias/13-db-porta-5432-fechada.txt)) |

### Serviço `web`

| Propriedade | Função |
|---|---|
| `build: ./app` | Constrói a imagem a partir do **Dockerfile próprio** em `./app`. Diferente de `image:`, que baixaria uma imagem pronta |
| `environment: DB_HOST: db ...` | As variáveis que o `app.py` lê. `DB_HOST: db` é o nome do serviço, resolvido pelo DNS interno. `DB_NAME/USER/PASSWORD` reutilizam os valores do `.env`. `UPLOAD_DIR: /app/uploads` |
| `ports: "8080:5000"` | `porta-do-host:porta-do-contêiner`. O navegador acessa `localhost:8080`; o Docker encaminha para a 5000 do Gunicorn |
| `volumes: fotos:/app/uploads` | Volume nomeado das fotos, no mesmo caminho que o `app.py` usa |
| `depends_on: db: condition: service_healthy` | O `web` só **inicia** depois que o `db` estiver `healthy` (RNF05) |
| `networks`, `restart` | Iguais aos do `db` |

### Blocos de topo

- `volumes: dados_banco, fotos` **declaram** os dois volumes nomeados; o Docker os cria no primeiro `up` com o prefixo do projeto (`achados-perdidos_dados_banco` e `achados-perdidos_fotos`).
- `networks: rede_interna: driver: bridge` cria uma rede *bridge definida pelo usuário*. Nesse tipo de rede o Docker mantém um DNS que resolve o nome de cada serviço; na bridge padrão (criada por `docker run` sem rede) não há resolução por nome, só por IP (Q1).

### `depends_on` e `service_healthy` (Q4)

Sem `condition`, o `depends_on` só garante a **ordem de início** dos processos, não que o PostgreSQL já esteja pronto para conexões; ele leva alguns segundos para inicializar o diretório de dados. O `web` poderia subir e falhar na primeira conexão. Com `service_healthy`, o `web` espera o `healthcheck` do `db` passar. A saída do `up` mostra a sequência: `db Healthy` e só depois `web Started` ([evidência 01](evidencias/01-compose-ps.txt)).

### Proteção das senhas (RNF03)

O `docker-compose.yml` usa apenas `${POSTGRES_PASSWORD}`, nunca o valor. O valor está no `.env`, que o `.gitignore` impede de ser versionado. O repositório contém o `.env.example`, com as mesmas chaves e valores fictícios.

---

## (c) O caminho de um `POST /itens` com foto

Comando usado ([evidência 05](evidencias/05-post-item.txt)):

```
curl.exe -F descricao="Carregador Samsung" -F local="Cantina" -F foto=@oculos.png http://localhost:8080/itens
```

1. O `curl` monta uma requisição HTTP `POST` do tipo `multipart/form-data`, com os campos `descricao`, `local` e o conteúdo do arquivo em `foto`, e a envia a `localhost:8080`.
2. O Docker Desktop recebe a conexão na porta **8080 do host** e a encaminha, pelo mapeamento `8080:5000`, para a porta **5000 do contêiner `web`**.
3. O **Gunicorn**, processo principal do contêiner, aceita a conexão e entrega a requisição a um worker.
4. O **Flask** roteia `POST /itens` para a função `cadastrar()`.
5. A função lê `descricao` e `local` de `request.form`. Se algum faltar, responde `400`.
6. Se há arquivo, gera um nome aleatório (`uuid4`), mantendo a extensão, e executa `foto.save(...)` em `/app/uploads/<uuid>.png`.
7. Como `/app/uploads` é o ponto de montagem do **volume `fotos`**, o arquivo é gravado fisicamente no volume (e não na camada gravável do contêiner), em `/var/lib/docker/volumes/achados-perdidos_fotos/_data` dentro da VM do Docker ([evidência 17](evidencias/17-volume-inspect.txt)).
8. O código chama `conectar()`, que abre uma conexão com o PostgreSQL usando `host=db`. O **DNS interno** da `rede_interna` resolve `db` para o IP do contêiner do banco, e a conexão segue pela rede para a porta 5432, com usuário e senha vindos das variáveis de ambiente.
9. Executa `INSERT INTO itens (descricao, local, foto) ... RETURNING id`. O PostgreSQL grava a linha no diretório de dados, montado no **volume `dados_banco`** (`/var/lib/postgresql/data`).
10. Ao sair do bloco `with`, a conexão confirma (commit) a transação.
11. O Flask responde `201` com `{"foto": "<uuid>.png", "id": 5}`, que volta ao `curl` pelo mesmo caminho.

Resultado: a **foto** está no volume `fotos`; o **registro** está no volume `dados_banco`, com o nome do arquivo como referência.

---

## (d) Ciclo de vida dos volumes

Dados registrados com `GET /estatisticas` antes de cada passo (evidências 08, 14 e 19):

| Passo | Comando | `itens_no_banco` | `fotos_no_volume` | O que aconteceu |
|---|---|:---:|:---:|---|
| Antes | cadastro de 2 itens com foto | 5 | 2 | 3 itens do `init.sql` + 2 cadastrados |
| 1. Recriação | `docker compose down` e `docker compose up -d` | 5 | 2 | `down` removeu os **contêineres e a rede**, mas não os volumes. O `up` criou contêineres novos e montou os mesmos volumes |
| 2. Inspeção | `docker volume ls` e `docker volume inspect` | n/a | n/a | Dois volumes existem; o `Mountpoint` de cada um fica dentro da VM do Docker (ver abaixo) |
| 3. Remoção | `docker compose down -v` e `docker compose up -d` | 3 | 0 | `-v` removeu também os volumes. O banco subiu vazio e executou o `init.sql` de novo |

**Passo 1: por que os dados persistem.** Contêineres são descartáveis: o que se grava na camada gravável deles morre com eles. Os dois diretórios que importam estão em volumes, que têm ciclo de vida independente. O `init.sql` **não** rodou de novo, porque o diretório de dados já continha dados; por isso os 3 itens de exemplo não foram duplicados ([evidência 15](evidencias/15-itens-apos-down-up.txt)).

**Passo 2: onde ficam fisicamente.** `docker volume inspect` mostra `Mountpoint: /var/lib/docker/volumes/achados-perdidos_fotos/_data` (e o equivalente para `dados_banco`). No Windows, o Docker Desktop executa o motor numa VM Linux, e esse caminho é dentro dela, não numa pasta comum do Windows ([evidência 17](evidencias/17-volume-inspect.txt)). O conteúdo do volume das fotos, listado por `docker compose exec web ls -l /app/uploads`, eram 2 arquivos `.png` pertencentes a `appuser` ([evidência 18](evidencias/18-ls-fotos.txt)). O dono é `appuser` porque, ao criar o volume vazio, o Docker copia para ele o conteúdo e as permissões da pasta que a imagem tem naquele caminho, definidas pelo `chown` do Dockerfile.

**Passo 3: por que os 3 itens de exemplo voltaram e os cadastrados não.** Os 3 itens de exemplo existem no **arquivo** `db/init.sql`, que fica no projeto (bind mount), fora do volume. Com o diretório de dados vazio, o PostgreSQL executou o script e recriou a tabela e esses 3 registros. Os 2 itens cadastrados e suas fotos existiam **somente nos volumes**; ao apagá-los, foram perdidos, e nada os recria. A pasta de fotos voltou vazia (`total 0`, [evidência 21](evidencias/21-ls-fotos-apos-down-v.txt)).

**Resumo do ciclo de vida:**

| Elemento | Criado em | Removido em |
|---|---|---|
| Contêineres e rede | `up` | `down` (com ou sem `-v`) |
| Volumes `dados_banco` e `fotos` | primeiro `up` | **somente** `down -v` (ou `docker volume rm`) |
| Imagem `achados-perdidos-web` | `up --build` | `docker image rm` (não é afetada por `down`) |
