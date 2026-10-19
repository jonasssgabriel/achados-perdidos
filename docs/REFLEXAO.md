# Reflexão e equivalência em nuvem

Respostas às questões da seção 5 da prova (3 a 8 linhas cada) e a tabela da seção 5.1.

## Questões de reflexão

### Q1. DNS interno

Por que o serviço `web` consegue se conectar ao banco usando o nome `db` em vez de um endereço IP? Quem resolve esse nome e o que mudaria se os contêineres fossem criados com `docker run` na rede bridge padrão?

O IP de um contêiner muda sempre que ele é recriado, então o `web` não pode guardar o endereço do banco. No `docker-compose.yml` ele usa `DB_HOST: db`, o nome do serviço, que não muda. Quem traduz esse nome para o IP atual é o DNS embutido do Docker. Na evidência `10-network-inspect.txt`, o `db` está em `172.20.0.2` e o `web` em `172.20.0.3`; em outra subida os números podem ser outros e o nome continua valendo. Esse DNS só existe em redes definidas pelo usuário, como a `rede_interna`. Com `docker run` na bridge padrão não há tradução, e os contêineres só se encontram pelo IP.

### Q2. Volume nomeado e bind mount

Qual a diferença entre um volume nomeado e um bind mount? Justifique por que o `init.sql` foi montado como bind mount e os dados do banco como volume nomeado.

Um volume nomeado é gerenciado pelo Docker e fica na VM dele (`/var/lib/docker/volumes/.../_data`, evidência `17-volume-inspect.txt`); sobrevive ao contêiner e não depende de pastas do computador. Um bind mount liga um arquivo ou pasta do meu PC ao contêiner. Os dados do banco usam o volume `dados_banco`, porque quem cuida deles é o PostgreSQL e o Docker, e assim funcionam em qualquer máquina. O `init.sql` é bind mount (`./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro`) porque é um arquivo do projeto, que eu edito e envio ao repositório; dentro de um volume ele não viajaria com o código, e o banco subiria sem a tabela. O `:ro` impede o contêiner de alterá-lo.

### Q3. Alterar o `init.sql` depois da primeira subida

A mudança é aplicada? Por quê? Como aplicar a alteração sem perder dados?

Não. A imagem do PostgreSQL só executa os arquivos de `/docker-entrypoint-initdb.d/` quando o diretório de dados está vazio, ou seja, na primeira subida. Depois o volume `dados_banco` já tem o banco e o script é ignorado, mesmo editado. As evidências mostram isso: depois de `down` e `up -d` os dados continuaram e os itens de exemplo não duplicaram (`14` e `15`); só depois de `down -v` o `init.sql` rodou de novo (`19`). Para aplicar a mudança sem perder dados, executo o comando direto no banco, como `ALTER TABLE itens ADD COLUMN ...` com `docker compose exec db psql`, ou uso uma ferramenta de migração.

### Q4. `depends_on` sem `service_healthy`

Por que `depends_on` sozinho não garante que a aplicação consiga se conectar ao banco na primeira tentativa?

O `depends_on` sozinho só garante a ordem de início: o `web` sobe depois que o processo do `db` foi iniciado. Mas iniciado não é pronto, porque o PostgreSQL leva alguns segundos para preparar os dados e abrir a porta, e a primeira conexão do `web` poderia falhar. No `docker-compose.yml` o `db` tem um `healthcheck` com `pg_isready` a cada 5 segundos, e o `web` usa `condition: service_healthy`. A evidência `22-up-sequencia.txt` mostra a ordem real: `db Healthy` e só depois `web Starting`.

### Q5. Ordem das instruções e cache de camadas

Como a ordem `COPY requirements.txt`, `RUN pip install` e `COPY app.py` influencia o tempo de build? O que acontece quando só o `app.py` muda?

O Docker guarda cada instrução como uma camada e reaproveita a que não mudou; quando uma camada muda, as seguintes são refeitas. Com `COPY requirements.txt`, `RUN pip install` e `COPY . .` nessa ordem, o `pip install` só roda de novo se o `requirements.txt` mudar. Quando só o `app.py` muda, apenas a cópia do código é refeita. No primeiro build o pip levou 6,8 s de um total de 9,1 s; no segundo, sem mudanças, as camadas 2 a 6 apareceram como `CACHED` e o build levou 0,5 s. Com `COPY . .` antes do pip, toda edição no código refaria o `pip install`.

### Q6. Porta 5432 e LGPD

Por que a porta 5432 não deve ser publicada no host? Considerando que as fotos podem mostrar documentos pessoais, relacione a configuração com a LGPD e proponha duas medidas adicionais de proteção.

Publicar a 5432 abriria o banco para qualquer máquina que alcançasse o host, e alguém poderia tentar adivinhar a senha. No `docker-compose.yml` o `db` não tem `ports:`, e o `curl` em `localhost:5432` falha (evidência `13`). Isso se liga à LGPD: as fotos podem mostrar documentos pessoais, e a lei exige proteção contra acesso indevido; isolar o banco reduz quem chega aos dados. Duas medidas a mais: HTTPS na frente da API, porque hoje o tráfego não é criptografado e uma foto de documento poderia ser interceptada; e guardar a senha num serviço de segredos, em vez do `.env` no disco.

### Q7. Três réplicas do `web`

O que acontece com `docker compose up -d --scale web=3`? O que seria necessário para rodar três réplicas? As réplicas poderiam compartilhar o volume `fotos` com segurança?

O comando falha. Na evidência `23-scale-web-3.txt` a `web-3` não inicia: `Bind for 0.0.0.0:8080 failed: port is already allocated`, porque o `ports: "8080:5000"` reserva a 8080 do host para um único contêiner. Para ter três réplicas é preciso tirar a porta fixa do `web` e pôr um balanceador na frente, como o nginx do extra. As fotos só poderiam compartilhar o volume no mesmo computador; em vários servidores um volume local não é compartilhado, e a foto enviada a uma réplica daria 404 nas outras. O correto é um armazenamento de objetos, como S3, Blob Storage ou Cloud Storage.

---

## 5.1 Do ambiente local para a nuvem

| Peça do ambiente local | Microsoft Azure | AWS | Google Cloud |
|---|---|---|---|
| Contêiner `web` | Azure Container Apps | Amazon ECS com AWS Fargate | Cloud Run |
| Contêiner `db` + volume `dados_banco` | Azure Database for PostgreSQL (Flexible Server) | Amazon RDS for PostgreSQL | Cloud SQL for PostgreSQL |
| Volume `fotos` | Azure Blob Storage | Amazon S3 | Cloud Storage |
| `rede_interna` | Virtual Network (VNet) com sub-redes e endpoint privado | VPC com sub-redes privadas e security groups | VPC com IP privado para o banco |
| Arquivo `.env` (segredos) | Azure Key Vault | AWS Secrets Manager | Secret Manager |
| Imagem construída localmente | Azure Container Registry | Amazon ECR | Artifact Registry |

Os serviços de armazenamento de objetos, banco relacional e rede virtual seguem o mapa de equivalência do Encontro 1 (slide 36) e o Encontro 4 (objeto, bloco e arquivo). Para o contêiner, os segredos e o registro de imagens usei a documentação de cada provedor, porque esses serviços não aparecem no mapa dos slides.

### Qual peça muda mais ao migrar, e por quê

A peça que mais muda é o volume `fotos`. O `app.py` grava as fotos com `foto.save(os.path.join(UPLOAD_DIR, ...))` e as devolve com `send_from_directory(UPLOAD_DIR, ...)`, ambos pressupondo um disco local. Para usar Azure Blob Storage, Amazon S3 ou Cloud Storage, esses dois trechos precisariam ser reescritos para chamar a API do serviço de objetos, e é a única peça do ambiente que exige alterar o código. Além disso, um disco local não serve para várias réplicas em servidores diferentes (Q7). O banco também muda, pois o contêiner `db` com o volume `dados_banco` daria lugar a um PostgreSQL gerenciado, com backup e alta disponibilidade, mas o código continua o mesmo: o `app.py` lê o endereço e as credenciais de variáveis de ambiente (`DB_HOST`, `DB_USER`, `DB_PASSWORD`), então basta trocar esses valores. O `.env` passaria para um serviço de segredos, a `rede_interna` para uma rede virtual privada, e a imagem para um registro de contêineres, todas trocas de infraestrutura sem mudar o código.
