import os
import io

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)

from . import db
from .models import Hospital, Contato, DadosHospital, ProdutoHospital
from .excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
)
from .pdf_report import build_hospital_report_pdf
from .auth import admin_required


bp = Blueprint("main", __name__)


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
# IMPORTAR HOSPITAIS DO EXCEL (UMA VEZ)
# ======================================================
@bp.route("/hospitais/importar_excel")
@admin_required
def importar_hospitais_excel():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    rows = load_hospitais_from_excel(data_dir)

    criados = 0
    for r in rows:
        nome = (r.get("nome_hospital") or "").strip()
        if not nome:
            continue

        existe = Hospital.query.filter_by(nome_hospital=nome).first()
        if existe:
            continue

        h = Hospital(
            nome_hospital=nome,
            endereco=r.get("endereco"),
            numero=str(r.get("numero") or ""),
            complemento=r.get("complemento"),
            cep=str(r.get("cep") or ""),
            cidade=r.get("cidade"),
            estado=r.get("estado"),
        )
        db.session.add(h)
        criados += 1

    db.session.commit()
    flash(f"Hospitais importados: {criados}", "success")
    return redirect(url_for("main.hospitais"))


# ======================================================
# NOVO / EDITAR HOSPITAL
# ======================================================
@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
    if request.method == "POST":
        hospital = Hospital(
            nome_hospital=request.form.get("nome_hospital"),
            endereco=request.form.get("endereco"),
            numero=request.form.get("numero"),
            complemento=request.form.get("complemento"),
            cep=request.form.get("cep"),
            cidade=request.form.get("cidade"),
            estado=request.form.get("estado"),
        )
        db.session.add(hospital)
        db.session.commit()
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=None)


@bp.route("/hospitais/<int:hospital_id>/editar", methods=["GET", "POST"])
def editar_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        hospital.nome_hospital = request.form.get("nome_hospital")
        hospital.endereco = request.form.get("endereco")
        hospital.numero = request.form.get("numero")
        hospital.complemento = request.form.get("complemento")
        hospital.cep = request.form.get("cep")
        hospital.cidade = request.form.get("cidade")
        hospital.estado = request.form.get("estado")
        db.session.commit()
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=hospital)


# ======================================================
# CONTATOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos")
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    return render_template("contatos.html", hospital=hospital, contatos=contatos_db)


@bp.route("/hospitais/<int:hospital_id>/contatos/importar_excel")
@admin_required
def importar_contatos_excel(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    rows = load_contatos_from_excel(data_dir)

    for r in rows:
        try:
            if int(r.get("id_hospital") or 0) != hospital_id:
                continue
        except ValueError:
            continue

        nome = (r.get("nome_contato") or "").strip()
        if not nome:
            continue

        existe = Contato.query.filter_by(
            hospital_id=hospital_id,
            nome_contato=nome
        ).first()
        if existe:
            continue

        db.session.add(
            Contato(
                hospital_id=hospital_id,
                hospital_nome=hospital.nome_hospital,
                nome_contato=nome,
                cargo=r.get("cargo"),
                telefone=r.get("telefone"),
            )
        )

    db.session.commit()
    return redirect(url_for("main.contatos", hospital_id=hospital_id))


# ======================================================
# DADOS DO HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/dados")
def dados_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    return render_template("dados_hospitais.html", hospital=hospital, dados=dados)


@bp.route("/hospitais/<int:hospital_id>/dados/importar_excel")
@admin_required
def importar_dados_excel(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    rows = load_dados_hospitais_from_excel(data_dir)

    row = None
    for r in rows:
        try:
            if int(r.get("id_hospital") or 0) == hospital_id:
                row = r
                break
        except ValueError:
            continue

    if not row:
        flash("Dados não encontrados no Excel.", "error")
        return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))

    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    if not dados:
        dados = DadosHospital(hospital_id=hospital_id)
        db.session.add(dados)

    dados.especialidade = row.get("Qual a especialidade do hospital?")
    dados.leitos = row.get("Quantos leitos?")
    dados.leitos_uti = row.get("Quantos leitos de UTI?")
    dados.dieta_padrao = row.get("Qual a dieta padrão utilizada no hospital?")

    db.session.commit()
    return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))


# ======================================================
# PRODUTOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/produtos")
def produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()
    return render_template("produtos_hospitais.html", hospital=hospital, produtos=produtos_db)


@bp.route("/hospitais/<int:hospital_id>/produtos/importar_excel")
@admin_required
def importar_produtos_excel(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    rows = load_produtos_hospitais_from_excel(data_dir)

    for r in rows:
        try:
            hid = int(r.get("hospital_id") or r.get("id_hospital") or 0)
        except ValueError:
            continue
        if hid != hospital_id:
            continue

        produto = (r.get("produto") or "").strip()
        if not produto:
            continue

        existe = ProdutoHospital.query.filter_by(
            hospital_id=hospital_id,
            produto=produto
        ).first()
        if existe:
            continue

        db.session.add(
            ProdutoHospital(
                hospital_id=hospital_id,
                nome_hospital=hospital.nome_hospital,
                produto=produto,
                quantidade=int(r.get("quantidade") or 0),
            )
        )

    db.session.commit()
    return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))


# ======================================================
# RELATÓRIOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/relatorios")
def relatorios(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    return render_template(
        "relatorios.html",
        hospital=hospital,
        contatos=contatos,
        dados=dados,
        produtos=produtos,
    )


@bp.route("/hospitais/<int:hospital_id>/relatorios/pdf")
def relatorio_pdf(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    pdf_bytes = build_hospital_report_pdf(hospital, contatos, dados, produtos)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"relatorio_hospital_{hospital_id}.pdf",
    )


# ======================================================
# IMPORTAR TUDO (ADMIN)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/importar_tudo")
@admin_required
def importar_tudo(hospital_id):
    importar_contatos_excel(hospital_id)
    importar_dados_excel(hospital_id)
    importar_produtos_excel(hospital_id)
    flash("Importação completa concluída.", "success")
    return redirect(url_for("main.hospitais"))
