# Diagrama de arquitetura

Mostra o host, a porta publicada, os dois contêineres, a rede, os dois volumes (com o caminho de montagem de cada um) e o bind mount do `init.sql`. Dentro do retângulo `rede_interna` está tudo que fica na rede interna; fora dela ficam o cliente, os volumes e o arquivo do projeto.

## Ambiente do enunciado (`docker compose up -d --build`)

```mermaid
flowchart LR
    cli["Navegador ou curl<br/>localhost:8080"]

    subgraph host["Host: Docker Desktop"]
        subgraph net["rede_interna (bridge definida pelo usuário)"]
            web["<b>web</b><br/>Flask + Gunicorn<br/>escuta 0.0.0.0:5000<br/>usuário appuser"]
            db[("<b>db</b><br/>postgres:16-alpine<br/>:5432, sem porta no host")]
        end
        vf[("volume <b>fotos</b><br/>montado em /app/uploads")]
        vd[("volume <b>dados_banco</b><br/>montado em /var/lib/postgresql/data")]
        sql["db/init.sql<br/>bind mount somente leitura<br/>em /docker-entrypoint-initdb.d/"]
    end

    cli -- "porta publicada 8080 → 5000" --> web
    web -- "SQL, host=db, porta 5432" --> db
    web --- vf
    db --- vd
    sql -. "executado só com o banco vazio" .-> db
```

| Elemento | Dentro da rede interna? | Porta publicada no host |
|---|---|---|
| `web` | Sim | 8080 (para a 5000 do contêiner) |
| `db` | Sim | nenhuma |
| Volumes `fotos` e `dados_banco` | Não são rede; são armazenamento do Docker | n/a |
| `db/init.sql` | Não; é um arquivo do projeto montado no `db` | n/a |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/arquitetura-dark.svg">
  <img alt="Diagrama de arquitetura do ambiente do enunciado" src="img/arquitetura-light.svg" width="100%">
</picture>

## Com nginx na frente (extra da seção 6)

Usa o arquivo `docker-compose.nginx.yml` somado ao principal. O `web` deixa de publicar porta, e só o `nginx` expõe a 8080.

```mermaid
flowchart LR
    cli["Navegador ou curl<br/>localhost:8080"]

    subgraph host["Host: Docker Desktop"]
        subgraph net["rede_interna (bridge definida pelo usuário)"]
            ng["<b>nginx</b><br/>nginx:alpine<br/>:80"]
            web["<b>web</b><br/>Flask + Gunicorn :5000<br/>sem porta no host"]
            db[("<b>db</b><br/>postgres:16-alpine<br/>:5432, sem porta no host")]
        end
        vf[("volume <b>fotos</b><br/>/app/uploads")]
        vd[("volume <b>dados_banco</b><br/>/var/lib/postgresql/data")]
        conf["nginx/default.conf<br/>bind mount somente leitura"]
        sql["db/init.sql<br/>bind mount somente leitura"]
    end

    cli -- "porta publicada 8080 → 80" --> ng
    ng -- "proxy_pass web:5000" --> web
    web -- "SQL, host=db" --> db
    web --- vf
    db --- vd
    conf -.-> ng
    sql -. "só com o banco vazio" .-> db
```

Neste modo o nginx também entrega a página de teste (`nginx/site/index.html`) na rota `/`, montada como bind mount somente leitura em `/usr/share/nginx/html`. As demais rotas seguem para o `web`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/arquitetura-nginx-dark.svg">
  <img alt="Diagrama de arquitetura com nginx na frente do web" src="img/arquitetura-nginx-light.svg" width="100%">
</picture>
