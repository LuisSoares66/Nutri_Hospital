import os
import io
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, send_file
)
from sqlalchemy import inspect, text

from app import db
from app.models import (
    Hospital, Contato, DadosHospital, ProdutoHospital, AppMeta
)

from app.excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel
)

from app.pdf_report import build_hospital_report_pdf
from app.auth import admin_required


bp = Blueprint("main", __name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ======================================================
# HOME
# ======================================================
@bp.route("/")
def index():
    return redirect(url_for("main.hospitais"))


# ======================================================
# LISTA DE HOSPITAIS
# ======================================================
@bp.route("/hospitais")
def hospitais():
    hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
    return render_template("hospitais.html", hospitais=hospitais_db)


# ======================================================
# NOVO HOSPITAL
# ======================================================
@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
    if request.method == "POST":
        h = Hospital(
            nome_hospital=request.form.get("nome_hospital"),
            endereco=request.form.get("endereco"),
            numero=request.form.get("numero"),
            complemento=request.form.get("complemento"),
            cep=request.form.get("cep"),
            cidade=request.form.get("cidade"),
            estado=request.form.get("estado"),
        )
        db.session.add(h)
        db.session.commit()
        flash("Hospital cadastrado com sucesso!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=None)


# ======================================================
# APAGAR HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/apagar", methods=["POST"])
def apagar_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    try:
        db.session.delete(hospital)
        db.session.commit()
        flash("Hospital removido com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao apagar hospital: {e}", "error")
    return redirect(url_for("main.hospitais"))


# ======================================================
# CONTATOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos")
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    return render_template(
        "contatos.html",
        hospital=hospital,
        contatos=contatos_db
    )


# ======================================================
# DADOS DO HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/dados", methods=["GET", "POST"])
def dados_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()

    if request.method == "POST":
        if not dados:
            dados = DadosHospital(hospital_id=hospital_id)
            db.session.add(dados)

        for field in request.form:
            if hasattr(dados, field):
                setattr(dados, field, request.form.get(field))

        db.session.commit()
        flash("Dados salvos com sucesso.", "success")
        return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))

    return render_template(
        "dados_hospitais.html",
        hospital=hospital,
        dados=dados
    )


# ======================================================
# PRODUTOS DO HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/produtos", methods=["GET", "POST"])
def produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    if request.method == "POST":
        p = ProdutoHospital(
            hospital_id=hospital_id,
            nome_hospital=hospital.nome_hospital,
            marca_planilha=request.form.get("marca_planilha"),
            produto=request.form.get("produto"),
            quantidade=int(request.form.get("quantidade") or 0),
        )
        db.session.add(p)
        db.session.commit()
        flash("Produto adicionado.", "success")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    return render_template(
        "produtos_hospitais.html",
        hospital=hospital,
        produtos=produtos_db
    )


# ======================================================
# RELATÓRIOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/relatorios")
def relatorios(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    return render_template(
        "relatorios.html",
        hospital=hospital,
        contatos=contatos_db,
        dados=dados,
        produtos=produtos_db
    )


# ======================================================
# RELATÓRIO PDF
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/relatorios/pdf")
def relatorio_pdf(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    pdf_bytes = build_hospital_report_pdf(
        hospital, contatos_db, dados, produtos_db
    )

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"relatorio_hospital_{hospital_id}.pdf"
    )


# ======================================================
# IMPORTAR EXCEL (UMA VEZ)
# ======================================================
@bp.route("/admin/importar_excel_uma_vez", methods=["POST"])
@admin_required
def importar_excel_uma_vez():
    done = AppMeta.query.filter_by(key="excel_import_done").first()
    if done:
        flash("Importação já realizada.", "warning")
        return redirect(url_for("main.hospitais"))

    # HOSPITAIS
    for r in load_hospitais_from_excel(DATA_DIR):
        nome = (r.get("nome_hospital") or "").strip()
        if not nome:
            continue
        if Hospital.query.filter_by(nome_hospital=nome).first():
            continue

        h = Hospital(
            nome_hospital=nome,
            endereco=r.get("endereco"),
            numero=r.get("numero"),
            complemento=r.get("complemento"),
            cep=r.get("cep"),
            cidade=r.get("cidade"),
            estado=r.get("estado"),
        )
        db.session.add(h)

    db.session.commit()

    db.session.add(AppMeta(key="excel_import_done", value="1"))
    db.session.commit()

    flash("Importação realizada com sucesso.", "success")
    return redirect(url_for("main.hospitais"))


# ======================================================
# RESET TOTAL DO BANCO
# ======================================================
@bp.route("/admin/reset_db", methods=["POST"])
@admin_required
def reset_db():
    reset_pass = os.getenv("RESET_DB_PASSWORD", "")
    typed = (request.form.get("reset_password") or "").strip()
    confirm = (request.form.get("confirm_text") or "").strip().upper()

    if typed != reset_pass or confirm != "APAGAR":
        flash("Senha ou confirmação inválida.", "error")
        return redirect(url_for("main.hospitais"))

    insp = inspect(db.engine)
    tables = insp.get_table_names()
    protected = {"alembic_version", "app_meta"}

    with db.engine.begin() as conn:
        for t in tables:
            if t not in protected:
                conn.execute(
                    text(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE;')
                )

    AppMeta.query.delete()
    db.session.commit()

    flash("Banco zerado com sucesso.", "success")
    return redirect(url_for("main.hospitais"))
