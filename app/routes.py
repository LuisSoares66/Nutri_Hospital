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
from .auth import admin_required
from .models import Hospital, Contato, DadosHospital, ProdutoHospital, AppMeta
from .excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
)
from .pdf_report import build_hospital_report_pdf


bp = Blueprint("main", __name__)


def _data_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


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
# NOVO / EDITAR HOSPITAL
# ======================================================
@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
    if request.method == "POST":
        hospital = Hospital(
            nome_hospital=(request.form.get("nome_hospital") or "").strip(),
            endereco=(request.form.get("endereco") or "").strip(),
            numero=(request.form.get("numero") or "").strip(),
            complemento=(request.form.get("complemento") or "").strip(),
            cep=(request.form.get("cep") or "").strip(),
            cidade=(request.form.get("cidade") or "").strip(),
            estado=(request.form.get("estado") or "").strip(),
        )
        if not hospital.nome_hospital:
            flash("Nome do hospital é obrigatório.", "error")
            return redirect(url_for("main.novo_hospital"))

        db.session.add(hospital)
        db.session.commit()
        flash("Hospital cadastrado com sucesso!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=None)


@bp.route("/hospitais/<int:hospital_id>/editar", methods=["GET", "POST"])
def editar_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        hospital.nome_hospital = (request.form.get("nome_hospital") or "").strip()
        hospital.endereco = (request.form.get("endereco") or "").strip()
        hospital.numero = (request.form.get("numero") or "").strip()
        hospital.complemento = (request.form.get("complemento") or "").strip()
        hospital.cep = (request.form.get("cep") or "").strip()
        hospital.cidade = (request.form.get("cidade") or "").strip()
        hospital.estado = (request.form.get("estado") or "").strip()

        if not hospital.nome_hospital:
            flash("Nome do hospital é obrigatório.", "error")
            return redirect(url_for("main.editar_hospital", hospital_id=hospital_id))

        db.session.commit()
        flash("Hospital atualizado!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=hospital)


# ======================================================
# CONTATOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos")#, methods=["GET", "POST"])
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        nome = (request.form.get("nome_contato") or "").strip()
        if not nome:
            flash("Nome do contato é obrigatório.", "error")
            return redirect(url_for("main.contatos", hospital_id=hospital_id))

        c = Contato(
            hospital_id=hospital_id,
            hospital_nome=hospital.nome_hospital,
            nome_contato=nome,
            cargo=(request.form.get("cargo") or "").strip(),
            telefone=(request.form.get("telefone") or "").strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash("Contato salvo!", "success")
        return redirect(url_for("main.contatos", hospital_id=hospital_id))

    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    return render_template("contatos.html", hospital=hospital, contatos=contatos_db)


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

        # Campos mínimos (seu template pode ter mais, você amplia depois)
        dados.especialidade = request.form.get("especialidade")
        dados.leitos = request.form.get("leitos")
        dados.leitos_uti = request.form.get("leitos_uti")
        dados.dieta_padrao = request.form.get("dieta_padrao")

        db.session.commit()
        flash("Dados salvos!", "success")
        return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))

    return render_template("dados_hospitais.html", hospital=hospital, dados=dados)


# ======================================================
# PRODUTOS DO HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/produtos")#, methods=["GET", "POST"])
def produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        produto = (request.form.get("produto") or "").strip()
        if not produto:
            flash("Produto é obrigatório.", "error")
            return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

        qtd_raw = (request.form.get("quantidade") or "0").strip()
        try:
            qtd = int(float(qtd_raw.replace(",", ".")))
        except ValueError:
            qtd = 0

        existe = ProdutoHospital.query.filter_by(hospital_id=hospital_id, produto=produto).first()
        if existe:
            flash("Este produto já existe para este hospital.", "error")
            return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

        db.session.add(
            ProdutoHospital(
                hospital_id=hospital_id,
                nome_hospital=hospital.nome_hospital,
                produto=produto,
                quantidade=qtd,
            )
        )
        db.session.commit()
        flash("Produto adicionado!", "success")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()
    return render_template("produtos_hospitais.html", hospital=hospital, produtos=produtos_db)


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
        produtos=produtos_db,
    )


@bp.route("/hospitais/<int:hospital_id>/relatorios/pdf", methods=["GET"])
def relatorio_pdf(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    pdf_bytes = build_hospital_report_pdf(hospital, contatos_db, dados, produtos_db)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"relatorio_hospital_{hospital_id}.pdf",
    )


# ======================================================
# IMPORTAR EXCEL — APENAS UMA VEZ (ADMIN)
# URL: /admin/importar_excel_uma_vez
# ======================================================
@bp.route("/admin/importar_excel_uma_vez", methods=["GET"])
@admin_required
def importar_excel_uma_vez():
    # trava persistente no banco
    flag = AppMeta.query.filter_by(key="excel_import_done").first()
    if flag and flag.value == "1":
        return "Importação BLOQUEADA: já foi importado uma vez.", 400

    data_dir = _data_dir()

    # 1) Hospitais
    hosp_rows = load_hospitais_from_excel(data_dir)
    # blindagem: se vier algo errado do loader, tenta normalizar
    if hosp_rows and isinstance(hosp_rows[0], str):
        return "Erro: hospitais.xlsx foi lido em formato inválido. Verifique o excel_loader.py.", 500

    for r in hosp_rows:
        nome = (r.get("nome_hospital") or "").strip()
        if not nome:
            continue

        # evita duplicar por nome
        existe = Hospital.query.filter_by(nome_hospital=nome).first()
        if existe:
            continue

        h = Hospital(
            nome_hospital=nome,
            endereco=(r.get("endereco") or "").strip(),
            numero=str(r.get("numero") or "").strip(),
            complemento=(r.get("complemento") or "").strip(),
            cep=str(r.get("cep") or "").strip(),
            cidade=(r.get("cidade") or "").strip(),
            estado=(r.get("estado") or "").strip(),
        )

        # se o excel tiver id_hospital numérico, mantém id
        raw_id = str(r.get("id_hospital") or "").strip()
        if raw_id.isdigit():
            h.id = int(raw_id)

        db.session.add(h)

    db.session.commit()

    # 2) Contatos (pode existir sem associação)
    cont_rows = load_contatos_from_excel(data_dir)
    for r in cont_rows:
        nome_contato = (r.get("nome_contato") or "").strip()
        if not nome_contato:
            continue

        raw_hid = str(r.get("id_hospital") or "").strip()
        hospital_id = int(raw_hid) if raw_hid.isdigit() else None

        telefone = (r.get("telefone") or "").strip()

        # evita duplicação simples
        existe = Contato.query.filter_by(
            hospital_id=hospital_id,
            nome_contato=nome_contato,
            telefone=telefone
        ).first()
        if existe:
            continue

        db.session.add(Contato(
            hospital_id=hospital_id,
            hospital_nome=(r.get("hospital_nome") or "").strip(),
            nome_contato=nome_contato,
            cargo=(r.get("cargo") or "").strip(),
            telefone=telefone,
        ))

    db.session.commit()

    # 3) Dados Hospital
    dados_rows = load_dados_hospitais_from_excel(data_dir)
    for r in dados_rows:
        raw_hid = str(r.get("id_hospital") or "").strip()
        if not raw_hid.isdigit():
            continue
        hid = int(raw_hid)

        dados = DadosHospital.query.filter_by(hospital_id=hid).first()
        if not dados:
            dados = DadosHospital(hospital_id=hid)
            db.session.add(dados)

        dados.especialidade = r.get("Qual a especialidade do hospital?")
        dados.leitos = str(r.get("Quantos leitos?") or "")
        dados.leitos_uti = str(r.get("Quantos leitos de UTI?") or "")
        dados.fatores_decisorios = r.get("Quais fatores são decisórios para o hospital escolher um determinado produto?")
        dados.prioridades_atendimento = r.get("Quais as prioridas do hospital para um atendimento nutricional de excelencia?")
        dados.certificacao = r.get("O hospital tem certificação ONA, CANADIAN, Joint Comission,...)?")
        dados.emtn = r.get("O hospital tem EMTN?")
        dados.emtn_membros = r.get("Se sim, quais os membro (nomes e especialidade)?")
        dados.dieta_padrao = r.get("Qual a dieta padrão utilizada no hospital?")

    db.session.commit()

    # 4) Produtos Hospital
    prod_rows = load_produtos_hospitais_from_excel(data_dir)
    for r in prod_rows:
        raw_hid = str(r.get("hospital_id") or r.get("id_hospital") or "").strip()
        if not raw_hid.isdigit():
            continue
        hid = int(raw_hid)

        produto = (r.get("produto") or "").strip()
        if not produto:
            continue

        qtd_raw = str(r.get("quantidade") or "0").strip()
        try:
            qtd = int(float(qtd_raw.replace(",", "."))) if qtd_raw else 0
        except ValueError:
            qtd = 0

        existe = ProdutoHospital.query.filter_by(hospital_id=hid, produto=produto).first()
        if existe:
            continue

        db.session.add(ProdutoHospital(
            hospital_id=hid,
            nome_hospital=(r.get("nome_hospital") or "").strip(),
            marca_planilha=(r.get("marca_planilha") or "").strip(),
            produto=produto,
            quantidade=qtd,
        ))

    db.session.commit()

    # grava flag para travar de vez
    if not flag:
        flag = AppMeta(key="excel_import_done", value="1")
        db.session.add(flag)
    else:
        flag.value = "1"
    db.session.commit()

    return "IMPORTAÇÃO OK: executada uma vez e travada."
