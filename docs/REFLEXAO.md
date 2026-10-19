# Reflexão e equivalência em nuvem

Respostas às questões da seção 5 da prova (3 a 8 linhas cada) e a tabela da seção 5.1.

## Questões de reflexão

### Q1. DNS interno

Por que o serviço `web` consegue se conectar ao banco usando o nome `db` em vez de um endereço IP? Quem resolve esse nome e o que mudaria se os contêineres fossem criados com `docker run` na rede bridge padrão?

O IP de um contêiner muda toda vez que ele é destruído e recriado, então o `web` não pode guardar o endereço do banco. No `docker-compose.yml` o `web` usa `DB_HOST: db`, o nome do serviço, que não muda. Quem traduz esse nome para o IP atual é o servidor DNS embutido do Docker, que atualiza a resposta sempre que o contêiner é recriado. Na evidência `10-network-inspect.txt`, na `achados-perdidos_rede_interna`, o `db` aparece em `172.20.0.2` e o `web` em `172.20.0.3`; amanhã esses números podem ser outros, e o nome `db` continua funcionando. Esse DNS só existe em redes definidas pelo usuário, como a `rede_interna`. Se os contêineres fossem criados com `docker run` na rede bridge padrão, essa tradução não existiria e eles só se encontrariam pelo IP.

### Q2. Volume nomeado e bind mount

Qual a diferença entre um volume nomeado e um bind mount? Por que o `init.sql` foi montado como bind mount e os dados do banco como volume nomeado?

Um volume nomeado é gerenciado pelo Docker e fica numa pasta da VM do Docker (`/var/lib/docker/volumes/.../_data`, como mostra `17-volume-inspect.txt`); sobrevive à destruição do contêiner e não depende de nenhuma pasta do computador. Um bind mount liga um arquivo ou pasta do meu PC ao contêiner: o arquivo real continua na minha pasta do projeto. No `docker-compose.yml`, os dados do banco usam o volume nomeado `dados_banco`, porque quem cuida deles é o PostgreSQL e o Docker, e assim funcionam em qualquer máquina. O `init.sql` usa bind mount (`./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro`) porque é um arquivo do projeto, que eu edito e que vai para o repositório. Dentro de um volume do Docker ele não viajaria com o código, e quem baixasse o repositório subiria um banco sem a tabela `itens`. O `:ro` deixa o contêiner só ler o arquivo, sem poder alterá-lo.

### Q3. Alterar o `init.sql` depois da primeira subida

A mudança é aplicada? Por quê? Como aplicar a alteração sem perder dados?

Não, a mudança não é aplicada. A imagem do PostgreSQL só executa os arquivos de `/docker-entrypoint-initdb.d/` quando o diretório de dados está vazio, ou seja, na primeira subida. Depois disso o volume `dados_banco` já contém o banco, e o script é ignorado, mesmo que eu edite o `init.sql`. Isso se vê nas evidências: depois de `down` e `up -d` os dados permaneceram (`14-estatisticas-apos-down-up.txt`) e os 3 itens de exemplo não foram duplicados; só depois de `down -v`, com o volume apagado, o `init.sql` rodou de novo (`19-estatisticas-apos-down-v.txt`). Para aplicar a alteração sem perder dados, executo o comando direto no banco, por exemplo `ALTER TABLE itens ADD COLUMN ...` com `docker compose exec db psql`, ou uso uma ferramenta de migração. A alternativa `down -v` recria tudo pelo `init.sql`, mas apaga os itens e as fotos cadastrados.

### Q4. `depends_on` sem `service_healthy`

Por que `depends_on` sozinho não garante que a aplicação consiga se conectar ao banco na primeira tentativa?

O `depends_on` sozinho só garante a ordem de início dos contêineres: o `web` é iniciado depois que o processo do `db` foi iniciado. Mas "iniciado" não significa "pronto para aceitar conexões", porque o PostgreSQL leva alguns segundos para preparar o diretório de dados e abrir a porta. Se o `web` tentasse conectar nesse intervalo, a primeira conexão poderia falhar. No `docker-compose.yml` o `db` tem um `healthcheck` que executa `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}` a cada 5 segundos, e o `web` usa `depends_on` com `condition: service_healthy`, então só inicia quando o banco responde. A evidência `22-up-sequencia.txt` mostra a ordem real: `db Started`, `db Waiting`, `db Healthy` e só depois `web Starting` e `web Started`; `01-compose-ps.txt` mostra o `db` com status `healthy`.

### Q5. Ordem das instruções e cache de camadas

Como a ordem `COPY requirements.txt`, `RUN pip install` e `COPY app.py` influencia o tempo de build? O que acontece quando só o `app.py` muda?

O Docker guarda cada instrução do Dockerfile como uma camada e reaproveita a camada se a instrução e os arquivos que ela usa não mudaram; quando uma camada muda, todas as seguintes são refeitas. Com a ordem `COPY requirements.txt`, `RUN pip install`, `COPY . .`, o `pip install` só é refeito se o `requirements.txt` mudar. Quando só o `app.py` muda, as camadas anteriores ao `COPY . .` continuam em cache e só o código é copiado de novo. No primeiro build deste projeto, o `pip install` levou 6,8 s dentro de um build de 9,1 s; no segundo build, sem alterações, as camadas 2 a 6 apareceram como `CACHED` e o build levou 0,5 s. Se a ordem fosse `COPY . .` antes do `pip install`, qualquer edição no `app.py` invalidaria a camada do `COPY` e forçaria o `pip install` a baixar todas as dependências de novo.

### Q6. Porta 5432 e LGPD

Por que a porta 5432 não deve ser publicada no host? Considerando que as fotos podem mostrar documentos pessoais, relacione a configuração com a LGPD e proponha duas medidas adicionais de proteção.

Publicar a 5432 abriria o banco para qualquer máquina que alcançasse o host, e alguém poderia tentar adivinhar a senha por tentativa e erro. No `docker-compose.yml` o serviço `db` não tem `ports:`, e a porta existe só dentro da `rede_interna`; o `curl` em `localhost:5432` falha (`13-db-porta-5432-fechada.txt`) e o `docker compose ps` mostra `5432/tcp` sem mapeamento para o host. Isso se relaciona com a LGPD porque as fotos podem mostrar documentos pessoais (carteira de estudante, RG), que são dados pessoais, e a lei exige medidas contra acesso indevido; manter o banco isolado reduz quem consegue chegar a eles. Duas medidas adicionais: (1) HTTPS na frente da API, porque hoje o tráfego em `localhost:8080` não é criptografado e uma foto de documento poderia ser interceptada na rede; (2) guardar a senha do banco num serviço de segredos (Azure Key Vault, AWS Secrets Manager ou Secret Manager do Google), em vez de um arquivo `.env` no disco, para controlar quem lê a credencial e poder trocá-la sem editar arquivos.

### Q7. Três réplicas do `web`

O que acontece com `docker compose up -d --scale web=3`? O que seria necessário para rodar três réplicas? As réplicas poderiam compartilhar o volume `fotos` com segurança?

O comando falha. Na evidência `23-scale-web-3.txt`, o Compose cria as réplicas `web-2` e `web-3`, mas o Docker recusa iniciar a `web-3` com `Bind for 0.0.0.0:8080 failed: port is already allocated`: o `ports: "8080:5000"` reserva a porta 8080 do host para um único contêiner, e a `web-1` já a usa. Depois do comando, o `docker compose ps` mostra só a `web-1` em execução. Para rodar três réplicas seria preciso retirar a publicação fixa da 8080 no `web` e colocar na frente um balanceador de carga (por exemplo um nginx ou o balanceador da nuvem) que distribua as requisições para as réplicas pela `rede_interna`. Quanto ao volume `fotos`: no mesmo computador as réplicas poderiam gravar no mesmo volume, mas em vários servidores um volume local não é compartilhado entre máquinas, e uma foto enviada para uma réplica não existiria para as outras (`GET /fotos/<nome>` daria 404 conforme o balanceador escolhesse a réplica). O correto na nuvem é guardar as fotos num armazenamento de objetos compartilhado, como Azure Blob Storage, Amazon S3 ou Cloud Storage, e não num volume local. O banco também precisaria ser acessado por todas as réplicas, o que o PostgreSQL já suporta por conexões.

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

> Observação: esta tabela é conhecimento complementar, não vem dos slides. Confirmar com o material da disciplina.

### Qual peça muda mais ao migrar, e por quê

A peça que mais muda é o volume `fotos`. O `app.py` grava as fotos com `foto.save(os.path.join(UPLOAD_DIR, ...))` e as devolve com `send_from_directory(UPLOAD_DIR, ...)`, ambos pressupondo um disco local. Para usar Azure Blob Storage, Amazon S3 ou Cloud Storage, esses dois trechos precisariam ser reescritos para chamar a API do serviço de objetos, e é a única peça do ambiente que exige alterar o código. Além disso, um disco local não serve para várias réplicas em servidores diferentes (Q7). O banco também muda, pois o contêiner `db` com o volume `dados_banco` daria lugar a um PostgreSQL gerenciado, com backup e alta disponibilidade, mas o código continua o mesmo: o `app.py` lê o endereço e as credenciais de variáveis de ambiente (`DB_HOST`, `DB_USER`, `DB_PASSWORD`), então basta trocar esses valores. O `.env` passaria para um serviço de segredos, a `rede_interna` para uma rede virtual privada, e a imagem para um registro de contêineres, todas trocas de infraestrutura sem mudar o código.
