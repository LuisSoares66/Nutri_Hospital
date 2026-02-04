import os
import io
from datetime import datetime

import pandas as pd

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


# ======================================================
# APP
# ======================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_123")


# ======================================================
# DATABASE CONFIG
# ======================================================
def get_database_uri():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url
    return "sqlite:///nutri_hospital.db"  # local (Windows)


app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ======================================================
# EXTENSIONS
# ======================================================
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ======================================================
# MODELS
# ======================================================
class Hospital(db.Model):
    __tablename__ = "hospitais"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------- Identificação --------
    nome_hospital = db.Column(db.String(200))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(50))
    cep = db.Column(db.String(20))
    telefone = db.Column(db.String(50))

    # -------- Contatos --------
    contato1_nome = db.Column(db.String(150))
    contato1_funcao = db.Column(db.String(150))
    contato1_telefone = db.Column(db.String(50))

    contato2_nome = db.Column(db.String(150))
    contato2_funcao = db.Column(db.String(150))
    contato2_telefone = db.Column(db.String(50))

    contato3_nome = db.Column(db.String(150))
    contato3_funcao = db.Column(db.String(150))
    contato3_telefone = db.Column(db.String(50))

    # -------- Questionário --------
    especialidade = db.Column(db.String(200))
    leitos = db.Column(db.Integer)
    leitos_uti = db.Column(db.Integer)

    fatores_decisorios = db.Column(db.Text)
    prioridades_excelencia = db.Column(db.Text)
    certificacoes = db.Column(db.Text)

    tem_emtn = db.Column(db.String(20))
    emtn_membros = db.Column(db.Text)

    tem_comissao_feridas = db.Column(db.String(20))
    comissao_feridas_membros = db.Column(db.Text)

    nutricao_enteral_dia = db.Column(db.Integer)
    pacientes_tno_dia = db.Column(db.Integer)

    altas_orientadas_periodo = db.Column(db.String(100))
    quem_orienta_alta = db.Column(db.Text)

    protocolo_evolucao_dieta = db.Column(db.Text)
    protocolo_suplementacao_feridas = db.Column(db.Text)

    maior_desafio = db.Column(db.Text)
    dieta_padrao = db.Column(db.Text)

    bomba_infusao = db.Column(db.Text)

    tem_convenio = db.Column(db.String(20))
    principais_convenios = db.Column(db.Text)
    modelo_pagamento = db.Column(db.Text)

    tem_reembolso = db.Column(db.String(20))

    modelo_compras = db.Column(db.Text)
    contrato_periodicidade = db.Column(db.String(50))
    nova_negociacao_quando = db.Column(db.Text)


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)


class HospitalProduto(db.Model):
    __tablename__ = "hospital_produtos"

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitais.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    quantidade = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hospital = db.relationship("Hospital", backref=db.backref("itens_produto", lazy=True))
    produto = db.relationship("Produto")


# ======================================================
# HELPERS
# ======================================================
def to_str(v):
    return "" if v is None else str(v).strip()


def to_int(v):
    try:
        if v is None or str(v).strip() == "":
            return None
        return int(v)
    except ValueError:
        return None


def produtos_excel_path():
    # /data/produtos.xlsx dentro do projeto
    return os.path.join(app.root_path, "data", "produtos.xlsx")


def sync_produtos_from_excel():
    """
    Carrega produtos do Excel /data/produtos.xlsx para a tabela Produto.
    - não apaga produtos existentes
    - adiciona novos automaticamente
    """
    path = produtos_excel_path()
    if not os.path.exists(path):
        # Não quebra o app, só avisa no log
        print(f"[AVISO] Arquivo de produtos não encontrado: {path}")
        return

    df = pd.read_excel(path, dtype=str)
    if df.empty:
        print("[AVISO] produtos.xlsx está vazio.")
        return

    # tenta achar uma coluna “Produto” ou “Nome”
    cols = [c.strip() for c in df.columns.astype(str).tolist()]
    col_escolhida = None
    for candidato in ["Produto", "produto", "Nome", "nome"]:
        if candidato in cols:
            col_escolhida = candidato
            break
    if col_escolhida is None:
        # usa primeira coluna
        col_escolhida = df.columns[0]

    nomes = (
        df[col_escolhida]
        .astype(str)
        .map(lambda x: x.strip())
        .replace({"nan": ""})
    )
    nomes = [n for n in nomes.tolist() if n]

    if not nomes:
        print("[AVISO] Nenhum nome de produto válido encontrado no Excel.")
        return

    # insere apenas os que não existem
    existentes = {p.nome for p in Produto.query.all()}
    novos = [n for n in nomes if n not in existentes]

    if novos:
        for n in novos:
            db.session.add(Produto(nome=n))
        db.session.commit()
        print(f"[OK] Produtos inseridos do Excel: {len(novos)}")
    else:
        print("[OK] Nenhum produto novo para inserir.")


@app.before_request
def ensure_produtos_loaded():
    """
    Carrega produtos automaticamente se a tabela estiver vazia.
    (evita ficar lendo Excel toda hora)
    """
    try:
        if Produto.query.count() == 0:
            sync_produtos_from_excel()
    except Exception as e:
        # não derruba o app
        print("[ERRO] Falha ao carregar produtos do Excel:", e)


# ======================================================
# ROTAS
# ======================================================
@app.route("/")
def home():
    total_hospitais = Hospital.query.count()
    ultimo_cadastro = Hospital.query.order_by(Hospital.created_at.desc()).first()
    return render_template(
        "index.html",
        total_hospitais=total_hospitais,
        ultimo_cadastro=ultimo_cadastro
    )


@app.route("/registro")
def registro():
    return render_template("registro.html")


@app.route("/registro/hospital", methods=["GET", "POST"])
def registro_hospital():
    if request.method == "POST":
        h = Hospital(
            nome_hospital=to_str(request.form.get("nome_hospital")),
            endereco=to_str(request.form.get("endereco")),
            numero=to_str(request.form.get("numero")),
            complemento=to_str(request.form.get("complemento")),
            cidade=to_str(request.form.get("cidade")),
            estado=to_str(request.form.get("estado")),
            cep=to_str(request.form.get("cep")),
            telefone=to_str(request.form.get("telefone")),

            contato1_nome=to_str(request.form.get("contato1_nome")),
            contato1_funcao=to_str(request.form.get("contato1_funcao")),
            contato1_telefone=to_str(request.form.get("contato1_telefone")),

            contato2_nome=to_str(request.form.get("contato2_nome")),
            contato2_funcao=to_str(request.form.get("contato2_funcao")),
            contato2_telefone=to_str(request.form.get("contato2_telefone")),

            contato3_nome=to_str(request.form.get("contato3_nome")),
            contato3_funcao=to_str(request.form.get("contato3_funcao")),
            contato3_telefone=to_str(request.form.get("contato3_telefone")),

            especialidade=to_str(request.form.get("especialidade")),
            leitos=to_int(request.form.get("leitos")),
            leitos_uti=to_int(request.form.get("leitos_uti")),
            fatores_decisorios=to_str(request.form.get("fatores_decisorios")),
            prioridades_excelencia=to_str(request.form.get("prioridades_excelencia")),
            certificacoes=to_str(request.form.get("certificacoes")),
            tem_emtn=to_str(request.form.get("tem_emtn")),
            emtn_membros=to_str(request.form.get("emtn_membros")),
            tem_comissao_feridas=to_str(request.form.get("tem_comissao_feridas")),
            comissao_feridas_membros=to_str(request.form.get("comissao_feridas_membros")),
            nutricao_enteral_dia=to_int(request.form.get("nutricao_enteral_dia")),
            pacientes_tno_dia=to_int(request.form.get("pacientes_tno_dia")),
            altas_orientadas_periodo=to_str(request.form.get("altas_orientadas_periodo")),
            quem_orienta_alta=to_str(request.form.get("quem_orienta_alta")),
            protocolo_evolucao_dieta=to_str(request.form.get("protocolo_evolucao_dieta")),
            protocolo_suplementacao_feridas=to_str(request.form.get("protocolo_suplementacao_feridas")),
            maior_desafio=to_str(request.form.get("maior_desafio")),
            dieta_padrao=to_str(request.form.get("dieta_padrao")),
            bomba_infusao=to_str(request.form.get("bomba_infusao")),
            tem_convenio=to_str(request.form.get("tem_convenio")),
            principais_convenios=to_str(request.form.get("principais_convenios")),
            modelo_pagamento=to_str(request.form.get("modelo_pagamento")),
            tem_reembolso=to_str(request.form.get("tem_reembolso")),
            modelo_compras=to_str(request.form.get("modelo_compras")),
            contrato_periodicidade=to_str(request.form.get("contrato_periodicidade")),
            nova_negociacao_quando=to_str(request.form.get("nova_negociacao_quando")),
        )

        db.session.add(h)
        db.session.commit()
        flash("Hospital cadastrado com sucesso!", "success")
        return redirect(url_for("leitura"))

    return render_template("hospital_form.html")


@app.route("/leitura")
def leitura():
    hospitais = Hospital.query.order_by(Hospital.created_at.desc()).all()
    return render_template("leitura.html", hospitais=hospitais)


# --------- NOVO: DETALHE DO HOSPITAL ----------
@app.route("/hospital/<int:hospital_id>")
def hospital_detalhe(hospital_id):
    h = Hospital.query.get_or_404(hospital_id)
    return render_template("hospital_detalhe.html", h=h)


# --------- NOVO: PRODUTOS DO HOSPITAL ----------
@app.route("/hospital/<int:hospital_id>/produtos", methods=["GET", "POST"])
def hospital_produtos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    # garante que existe lista de produtos
    if Produto.query.count() == 0:
        sync_produtos_from_excel()

    produtos = Produto.query.order_by(Produto.nome.asc()).all()

    if request.method == "POST":
        produto_id = to_int(request.form.get("produto_id"))
        quantidade = to_int(request.form.get("quantidade"))

        if not produto_id:
            flash("Selecione um produto.", "error")
            return redirect(url_for("hospital_produtos", hospital_id=hospital_id))

        if quantidade is None or quantidade < 0:
            flash("Informe uma quantidade válida (0 ou mais).", "error")
            return redirect(url_for("hospital_produtos", hospital_id=hospital_id))

        # se já existe lançamento para esse hospital+produto, soma
        existente = HospitalProduto.query.filter_by(
            hospital_id=hospital_id,
            produto_id=produto_id
        ).first()

        if existente:
            existente.quantidade = (existente.quantidade or 0) + quantidade
        else:
            db.session.add(HospitalProduto(
                hospital_id=hospital_id,
                produto_id=produto_id,
                quantidade=quantidade
            ))

        db.session.commit()
        flash("Produto salvo com sucesso!", "success")
        return redirect(url_for("hospital_produtos", hospital_id=hospital_id))

    itens = (
        HospitalProduto.query
        .filter_by(hospital_id=hospital_id)
        .join(Produto, Produto.id == HospitalProduto.produto_id)
        .order_by(Produto.nome.asc())
        .all()
    )

    return render_template(
        "hospital_produtos.html",
        hospital=hospital,
        produtos=produtos,
        itens=itens
    )


@app.route("/hospital/<int:hospital_id>/produtos/<int:item_id>/remover", methods=["POST"])
def hospital_produto_remover(hospital_id, item_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    item = HospitalProduto.query.filter_by(id=item_id, hospital_id=hospital.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removido.", "success")
    return redirect(url_for("hospital_produtos", hospital_id=hospital.id))


@app.route("/relatorios")
def relatorios():
    total = Hospital.query.count()
    media_leitos = db.session.query(func.avg(Hospital.leitos)).scalar()
    media_uti = db.session.query(func.avg(Hospital.leitos_uti)).scalar()

    top_especialidades = (
        db.session.query(Hospital.especialidade, func.count(Hospital.id))
        .group_by(Hospital.especialidade)
        .order_by(func.count(Hospital.id).desc())
        .limit(5)
        .all()
    )

    hospitais = Hospital.query.order_by(Hospital.created_at.desc()).all()

    return render_template(
        "relatorios.html",
        total=total,
        media_leitos=media_leitos,
        media_uti=media_uti,
        top_especialidades=top_especialidades,
        hospitais=hospitais
    )


@app.route("/relatorios/pdf")
def relatorios_pdf():
    hospitais = Hospital.query.order_by(Hospital.created_at.desc()).all()

    buffer = io.BytesIO()
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    margem = 12 * mm
    y = height - margem

    def line(txt, bold=False):
        nonlocal y
        if y < 20 * mm:
            c.showPage()
            y = height - margem
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawString(margem, y, txt)
        y -= 5 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margem, y, "Nutri_Hospital - Relatório (Hospitais)")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margem, y, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 10 * mm

    for h in hospitais:
        nome = h.nome_hospital or "Hospital (sem nome)"
        cidade_uf = f"{h.cidade or ''}/{h.estado or ''}".strip("/")
        line(f"{nome} — {cidade_uf} — ID {h.id}", bold=True)
        line(f"Telefone: {h.telefone or '-'}")
        line(f"Contato 1: {h.contato1_nome or '-'} | {h.contato1_funcao or '-'} | {h.contato1_telefone or '-'}")
        line("-" * 120)

    c.save()
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="relatorio_hospitais.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
