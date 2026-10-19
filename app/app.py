import os, uuid, socket
import psycopg
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
DB_URL = (f"host={os.getenv('DB_HOST', 'db')} port={os.getenv('DB_PORT', '5432')} "
          f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} "
          f"password={os.getenv('DB_PASSWORD')}")

def conectar():
    return psycopg.connect(DB_URL)

@app.get("/health")
def health():
    try:
        with conectar() as c:
            c.execute("SELECT 1")
        return jsonify(status="ok", banco="conectado", container=socket.gethostname())
    except Exception as e:
        return jsonify(status="erro", banco=str(e)), 503

@app.get("/itens")
def listar():
    local = request.args.get("local")
    sql = "SELECT id, descricao, local, foto, criado_em FROM itens"
    params = []
    if local:
        sql += " WHERE local ILIKE %s"
        params.append(f"%{local}%")
    with conectar() as c:
        linhas = c.execute(sql + " ORDER BY criado_em DESC", params).fetchall()
    return jsonify([
        {"id": l[0], "descricao": l[1], "local": l[2],
         "foto": f"/fotos/{l[3]}" if l[3] else None, "criado_em": l[4].isoformat()}
        for l in linhas])

@app.post("/itens")
def cadastrar():
    descricao = request.form.get("descricao")
    local = request.form.get("local")
    if not descricao or not local:
        return jsonify(erro="campos 'descricao' e 'local' sao obrigatorios"), 400
    nome_foto = None
    foto = request.files.get("foto")
    if foto and foto.filename:
        ext = os.path.splitext(foto.filename)[1].lower()
        nome_foto = f"{uuid.uuid4().hex}{ext}"
        foto.save(os.path.join(UPLOAD_DIR, nome_foto))
    with conectar() as c:
        novo_id = c.execute(
            "INSERT INTO itens (descricao, local, foto) VALUES (%s, %s, %s) RETURNING id",
            (descricao, local, nome_foto)).fetchone()[0]
    return jsonify(id=novo_id, foto=nome_foto), 201

@app.get("/fotos/<nome>")
def foto(nome):
    return send_from_directory(UPLOAD_DIR, nome)

@app.get("/estatisticas")
def estatisticas():
    with conectar() as c:
        total = c.execute("SELECT COUNT(*) FROM itens").fetchone()[0]
    arquivos = len(os.listdir(UPLOAD_DIR))
    return jsonify(itens_no_banco=total, fotos_no_volume=arquivos)
