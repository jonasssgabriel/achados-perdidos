# Legendas das evidências

Cada arquivo desta pasta é a saída real de um comando executado neste ambiente. A coluna "Tarefa" indica a parte da prova a que a evidência se refere.

| Arquivo | Tarefa | Legenda |
|---|---|---|
| `34-up-build.txt` | 4 | Saída do `docker compose up -d --build`: a imagem do `web` construída a partir do Dockerfile e o `db` `Healthy` com o `web` em execução |
| `01-compose-ps.txt` | 4 | `docker compose ps`: `db` com status `healthy` e `web` em execução com a porta `8080->5000`; o `db` mostra só `5432/tcp`, sem porta publicada no host |
| `02-health.txt` | 4 (RF01) | `GET /health` responde `status: ok` e `banco: conectado` |
| `03-itens.txt` | 4 (RF02) | `GET /itens` lista os 3 itens de exemplo criados pelo `init.sql` |
| `04-itens-filtro.txt` | 4 (RF02) | `GET /itens?local=biblio` devolve só o item cujo local contém "biblio" |
| `05-post-item.txt` | 4 (RF03) | `POST /itens` com foto devolve `id` 5 e o nome da foto gerado pelo servidor |
| `06-itens-depois-post.txt` | 4 | `GET /itens` depois do cadastro: 5 itens, 2 deles com campo `foto` |
| `07-foto-no-navegador.png` | 4 (RF04) | Foto aberta no navegador em `localhost:8080/fotos/<nome>` |
| `08-estatisticas.txt` | 4 e 5 | `GET /estatisticas` antes dos testes de persistência: 5 itens no banco e 2 fotos no volume |
| `09-logs-web.txt` | 4 | `docker compose logs web`: o Gunicorn 23.0.0 escutando em `0.0.0.0:5000` |
| `10-network-inspect.txt` | A4 | `docker network inspect` da `rede_interna`: driver bridge, com `db` (172.20.0.2) e `web` (172.20.0.3) |
| `11-image-ls.txt` | A4 | `docker image ls` mostrando o tamanho da imagem `achados-perdidos-web` |
| `12-whoami.txt` | RNF04 | `docker compose exec web whoami` retorna `appuser`, não `root` |
| `13-db-porta-5432-fechada.txt` | RNF, Q6 | `curl` em `localhost:5432` falha: o banco não está acessível do host |
| `14-estatisticas-apos-down-up.txt` | 5.1 | Depois de `down` e `up -d`: continuam 5 itens e 2 fotos |
| `15-itens-apos-down-up.txt` | 5.1 | `GET /itens` depois de `down` e `up -d`: os mesmos itens, sem duplicar os de exemplo |
| `16-volume-ls.txt` | 5.2 | `docker volume ls`: os volumes `achados-perdidos_dados_banco` e `achados-perdidos_fotos` |
| `17-volume-inspect.txt` | 5.2 | `docker volume inspect`: o `Mountpoint` de cada volume, dentro da VM do Docker |
| `18-ls-fotos.txt` | 5.2 | `ls -l /app/uploads` no contêiner `web`: 2 fotos, com dono `appuser` |
| `19-estatisticas-apos-down-v.txt` | 5.3 | Depois de `down -v` e `up -d`: 3 itens e 0 fotos |
| `20-itens-apos-down-v.txt` | 5.3 | `GET /itens` depois de `down -v`: só os 3 itens de exemplo do `init.sql` |
| `21-ls-fotos-apos-down-v.txt` | 5.3 | `ls -l /app/uploads` depois de `down -v`: pasta de fotos vazia (`total 0`) |
| `22-up-sequencia.txt` | Q4 | Saída do `docker compose up -d`: o `db` fica `Healthy` antes do `web` iniciar |
| `23-scale-web-3.txt` | Q7 | `docker compose up -d --scale web=3` falha: `Bind for 0.0.0.0:8080 failed: port is already allocated` |
| `24-adminer-profile-debug.txt` | Bônus Adminer | `docker compose --profile debug ps`: com o profile aparecem `adminer`, `db` e `web` |
| `25-sem-profile-so-web-db.txt` | Bônus Adminer | `docker compose ps` sem o profile: o Adminer não existe, só `db` e `web` |
| `26-adminer-tabela-itens.png` | Bônus Adminer | Adminer em `localhost:8081` conectado ao `db`, mostrando a tabela `itens` |
| `27-backup-origem-ls.txt` | Bônus backup | `ls -l` do volume `fotos` original: 1 foto de 17.938 bytes |
| `28-backup-arquivo.txt` | Bônus backup | `dir backup`: o arquivo `fotos.tar.gz` com 18.109 bytes |
| `29-restauracao-ls.txt` | Bônus backup | `ls -l` do volume novo `fotos_restaurado`: a mesma foto, com o mesmo tamanho |
| `30-nginx-ps.txt` | Bônus nginx | Só o `nginx` publica porta (`8080->80`); `web` e `db` sem porta no host |
| `31-nginx-health-header.txt` | Bônus nginx | `curl -i /health` com `Server: nginx/1.31.7`: a resposta passou pelo proxy |
| `32-nginx-estatisticas.txt` | Bônus nginx | Cadastro de foto através do proxy: 5 itens no banco e 2 fotos no volume |
| `33-pagina-web.jpg` | Bônus nginx | Página de teste em `localhost:8080` servida pelo nginx: API conectada, 5 itens, 2 fotos, atalhos de filtro e terminal com os `curl` equivalentes |
