# Roteiro de demonstração

Sequência para mostrar o ambiente funcionando, com o resultado esperado de cada comando e a frase que o explica. Todos os comandos rodam na pasta do projeto, no Prompt de Comando (`cmd`) ou no PowerShell. No PowerShell, `curl` vira `curl.exe`.

## Antes de começar

- Docker Desktop aberto (o `docker version` mostra Client e Server).
- Na pasta `achados-perdidos`, com o arquivo `.env` presente (copiado do `.env.example`).
- Ambiente no ar: `docker compose up -d --build`.

Não rodar durante a demonstração, a não ser que peçam: `docker compose down -v`. Ele apaga os itens e as fotos. Se for pedido, avisar antes e lembrar que os três itens de exemplo voltam porque estão no `init.sql`.

## 1. Subir e ver os contêineres

```
docker compose up -d --build
docker compose ps
```

Esperado: `db` com `(healthy)` e `web` com `0.0.0.0:8080->5000/tcp`. O `db` mostra só `5432/tcp`, sem seta.

> "O `web` publica a 8080 no meu computador e encaminha para a 5000 do contêiner. O banco não publica nada: só é alcançável dentro da rede."

## 2. A aplicação responde e fala com o banco

```
curl http://localhost:8080/health
```

Esperado: `"banco":"conectado"` e `"status":"ok"`.

> "O `/health` faz um `SELECT 1` no banco. Mostra que o `web` realmente conversa com o PostgreSQL, e não só que o processo está de pé."

## 3. Objetos cadastrados

```
curl http://localhost:8080/itens
curl "http://localhost:8080/itens?local=biblio"
curl http://localhost:8080/estatisticas
```

Esperado: os itens em JSON; o filtro devolve só a "Garrafa termica azul"; as estatísticas mostram 5 itens e 2 fotos.

## 4. Cadastro com foto

```
curl -F descricao="Mochila verde" -F local="Quadra" -F foto=@oculos.png http://localhost:8080/itens
curl http://localhost:8080/estatisticas
```

Esperado: resposta `201` com um `id` e o nome da foto (um código aleatório), e as estatísticas com um item e uma foto a mais. Abrir no navegador `http://localhost:8080/fotos/<nome devolvido>` para mostrar a imagem.

> "A foto vai para o volume `fotos`, e o registro vai para o banco. O nome é um UUID para duas fotos iguais nunca se sobrescreverem."

(O arquivo `oculos.png` não está no repositório. Usar qualquer imagem do computador.)

## 5. Usuário sem privilégios

```
docker compose exec web whoami
```

Esperado: `appuser`.

> "O `USER appuser` do Dockerfile faz o processo rodar sem ser root. Se a aplicação for invadida, o invasor não é administrador do contêiner."

## 6. Rede interna e DNS

```
docker network inspect achados-perdidos_rede_interna --format "{{range .Containers}}{{.Name}}  {{.IPv4Address}}{{println}}{{end}}"
```

Esperado: os dois contêineres, cada um com um IP (por exemplo `172.20.0.2` e `172.20.0.3`).

> "O `web` não usa o IP, usa o nome `db`. O IP muda quando o contêiner é recriado; o DNS interno do Docker traduz o nome para o IP atual. Esse DNS só existe em redes criadas pelo usuário, como a `rede_interna`."

## 7. Banco isolado

```
curl --max-time 3 http://localhost:5432
```

Esperado: falha de conexão (`Failed to connect`).

> "A porta 5432 não está publicada no host. Quem quiser chegar ao banco precisa estar dentro da rede, e só o `web` está."

## 8. Persistência (sem apagar nada)

```
docker compose down
docker compose up -d
curl http://localhost:8080/estatisticas
```

Esperado: os mesmos números de antes do `down`.

> "O `down` removeu contêineres e rede, mas os volumes ficam. Os dois diretórios que importam, o do banco e o das fotos, estão em volumes nomeados, que vivem mais que os contêineres."

## 9. Onde os dados ficam

```
docker volume ls
docker volume inspect achados-perdidos_fotos --format "{{.Name}}  {{.Mountpoint}}"
docker compose exec web ls -l /app/uploads
```

Esperado: os volumes `achados-perdidos_dados_banco` e `achados-perdidos_fotos`; o `Mountpoint` em `/var/lib/docker/volumes/.../_data`; as fotos listadas com dono `appuser`.

> "O volume fica dentro da VM do Docker Desktop, não numa pasta comum do Windows. O dono das fotos é `appuser` porque o `chown` do Dockerfile definiu isso e o volume vazio herda do que a imagem tem naquele caminho."

## 10. Organização do projeto

```
tree /F docs
```

Mostrar também o `README.md` no GitHub, o `docs/RELATORIO.md`, o `docs/REFLEXAO.md` e a pasta `docs/evidencias/` com a `LEGENDAS.md`.

## 11. Extras, se houver tempo

| Extra | Comando | O que mostrar |
|---|---|---|
| Adminer | `docker compose --profile debug up -d` e abrir `http://localhost:8081` (Sistema PostgreSQL, servidor `db`) | A tabela `itens`. Sem o profile, o Adminer não existe |
| nginx | `docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d` e abrir `http://localhost:8080` | A página com o terminal; no `docker compose ps` só o nginx publica porta |
| Backup | Comandos de `docs/EXTRAS.md` | `fotos.tar.gz` e a restauração no volume `fotos_restaurado` |

Para voltar ao modo do enunciado depois do nginx: `docker compose up -d --remove-orphans`.

## Perguntas prováveis e onde está a resposta

| Pergunta | Onde mostrar |
|---|---|
| Por que `depends_on` com `service_healthy`? | `docker-compose.yml` e a evidência `22-up-sequencia.txt` |
| Por que o `COPY requirements.txt` vem antes do código? | `app/Dockerfile` e a Q5 em `docs/REFLEXAO.md` |
| O que acontece com `--scale web=3`? | Evidência `23-scale-web-3.txt` e a Q7 |
| Por que o `init.sql` não atualiza um banco existente? | Q3 em `docs/REFLEXAO.md` |
| Onde está a senha? | Só no `.env`, que o `.gitignore` impede de ir ao Git; no repositório há o `.env.example` |

## Erros comuns na hora

- `curl` no PowerShell não é o `curl` de verdade: usar `curl.exe`.
- A porta 8080 ocupada: outro contêiner ou programa a usa (por exemplo, o modo nginx ligado ao mesmo tempo).
- Docker Desktop fechado: nenhum comando `docker` responde.
- No Adminer, esquecer de trocar o Sistema de MySQL para PostgreSQL: dá `Connection refused`.
