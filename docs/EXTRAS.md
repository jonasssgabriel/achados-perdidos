# Desafios bônus (seção 6 da prova)

Os três extras foram feitos sem alterar o ambiente principal: o Adminer fica atrás de um profile, o backup usa contêineres temporários, e o nginx entra num arquivo Compose separado. Por isso as evidências 01 a 23 continuam válidas para o `docker compose up -d --build` do enunciado.

## 1. Painel do banco com Adminer

O serviço `adminer` está no `docker-compose.yml` com `profiles: ["debug"]`. Um serviço de profile não é criado pelo `up` normal; só sobe quando o profile é pedido.

```
docker compose --profile debug up -d
```

Abra `http://localhost:8081`, escolha **Sistema: PostgreSQL**, servidor `db`, e use o usuário, a senha e o banco do `.env`. Se o sistema ficar em MySQL (o padrão do Adminer), a conexão falha com `Connection refused`, porque ele tenta falar o protocolo do MySQL com o PostgreSQL.

O Adminer está na `rede_interna` e encontra o banco pelo nome `db`, como o `web`. Publica a porta 8081 e não a 8080, que já é do `web`.

| Evidência | O que mostra |
|---|---|
| `24-adminer-profile-debug.txt` | Com o profile, aparecem `adminer`, `db` e `web` |
| `25-sem-profile-so-web-db.txt` | Sem o profile, só `db` e `web` |
| `26-adminer-tabela-itens.png` | A tabela `itens` aberta no Adminer |

## 2. Backup e restauração do volume `fotos`

Um contêiner temporário (`--rm`) monta o volume e uma pasta do computador e empacota o conteúdo num `.tar.gz`. O volume fica dentro da VM do Docker, então é pelo contêiner que se chega aos arquivos.

```
mkdir backup
docker run --rm -v achados-perdidos_fotos:/dados:ro -v "%cd%\backup":/backup alpine tar czf /backup/fotos.tar.gz -C /dados .
```

Restauração em um volume novo:

```
docker volume create fotos_restaurado
docker run --rm -v fotos_restaurado:/dados -v "%cd%\backup":/backup:ro alpine tar xzf /backup/fotos.tar.gz -C /dados
docker run --rm -v fotos_restaurado:/dados alpine ls -l /dados
```

No PowerShell, troque `%cd%` por `${PWD}`. O volume de origem é montado com `:ro` para o backup não alterar nada, e a pasta `backup` é montada com `:ro` na restauração.

| Evidência | O que mostra |
|---|---|
| `27-backup-origem-ls.txt` | A foto no volume original |
| `28-backup-arquivo.txt` | O arquivo `fotos.tar.gz` (18.109 bytes) |
| `29-restauracao-ls.txt` | A mesma foto (17.938 bytes) no volume novo `fotos_restaurado` |

A pasta `backup/` está no `.gitignore`, porque contém fotos de teste.

## 3. Proxy reverso com nginx

O arquivo `docker-compose.nginx.yml` é somado ao principal. Ele apaga a publicação de portas do `web` (`ports: !reset []`) e cria o serviço `nginx`, que passa a ser o único com porta publicada (`8080:80`). A configuração está em `nginx/default.conf` e é montada como bind mount somente leitura.

```
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
docker compose -f docker-compose.yml -f docker-compose.nginx.yml ps
curl -i http://localhost:8080/health
```

O `proxy_pass http://web:5000` usa o nome do serviço, resolvido pelo DNS da `rede_interna`. O `client_max_body_size 10m` permite uploads de foto de até 10 MB; o padrão do nginx é 1 MB. Para voltar ao ambiente do enunciado: `docker compose up -d --remove-orphans`.

| Evidência | O que mostra |
|---|---|
| `30-nginx-ps.txt` | Só o `nginx` publica porta (`8080->80`); `web` mostra `5000/tcp` e `db` mostra `5432/tcp`, sem mapeamento |
| `31-nginx-health-header.txt` | `Server: nginx/1.31.7` na resposta do `/health`: passou pelo proxy |
| `32-nginx-estatisticas.txt` | Cadastro com foto pelo proxy: 5 itens e 2 fotos |

### Página de teste (`nginx/site/index.html`)

No modo nginx, abrir `http://localhost:8080/` mostra uma página web que usa a própria API: indica se a API está conectada ao banco (`/health`), mostra as estatísticas (`/estatisticas`), lista os objetos com foto (`/itens` e `/fotos/<nome>`), filtra por local (`/itens?local=`, também por atalhos, um por local cadastrado) e cadastra objetos pelo formulário (`POST /itens`).

Ao lado do título há um terminal que registra cada requisição feita pela página como o comando `curl` equivalente, com o status HTTP, o tempo e um trecho da resposta. Cada comando vem com um comentário dizendo qual função do `app.py` o atende (por exemplo `listar()` para `GET /itens`), e clicar no comando o copia para rodar num terminal de verdade.

- É um único arquivo HTML, com CSS e JavaScript dentro, sem biblioteca nem fonte externa. Funciona sem internet.
- O nginx entrega o arquivo só na raiz exata (`location = /`); todas as outras rotas continuam indo para a API. Por isso a página chama a API no mesmo endereço, e o navegador não bloqueia por CORS. O `app.py` não foi alterado.
- O texto vindo do banco entra na página por `textContent`, e não por `innerHTML`, para uma descrição com HTML não ser executada.
- O banco grava `criado_em` em UTC, sem fuso; a página converte para o horário do navegador.
- O arquivo é montado no `nginx` como bind mount somente leitura (`./nginx/site:/usr/share/nginx/html:ro`).

| Evidência | O que mostra |
|---|---|
| `33-pagina-web.jpg` | A página com a API conectada, 5 itens e 2 fotos, os atalhos de filtro e o terminal com os comandos `curl` de `/health`, `/estatisticas` e `/itens` |

O diagrama atualizado está em [`arquitetura.md`](arquitetura.md).
