from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from . import db
from .models import Hospital, Contato, DadosHospital, ProdutoHospital

# Se você tiver o pdf_report.py
try:
    from .pdf_report import build_hospital_report_pdf
except Exception:
    build_hospital_report_pdf = None

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
# NOVO HOSPITAL
# ======================================================
@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
    if request.method == "POST":
        nome = (request.form.get("nome_hospital") or "").strip()
        if not nome:
            flash("Informe o nome do hospital.", "error")
            return redirect(url_for("main.novo_hospital"))

        hospital = Hospital(
            nome_hospital=nome,
            endereco=request.form.get("endereco"),
            numero=request.form.get("numero"),
            complemento=request.form.get("complemento"),
            cep=request.form.get("cep"),
            cidade=request.form.get("cidade"),
            estado=request.form.get("estado"),
        )
        db.session.add(hospital)
        db.session.commit()
        flash("Hospital cadastrado com sucesso!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=None)


# ======================================================
# EDITAR HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/editar", methods=["GET", "POST"])
def editar_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        hospital.nome_hospital = (request.form.get("nome_hospital") or "").strip()
        hospital.endereco = request.form.get("endereco")
        hospital.numero = request.form.get("numero")
        hospital.complemento = request.form.get("complemento")
        hospital.cep = request.form.get("cep")
        hospital.cidade = request.form.get("cidade")
        hospital.estado = request.form.get("estado")

        if not hospital.nome_hospital:
            flash("Informe o nome do hospital.", "error")
            return redirect(url_for("main.editar_hospital", hospital_id=hospital_id))

        db.session.commit()
        flash("Hospital atualizado com sucesso!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=hospital)


# ======================================================
# CONTATOS (ASSOCIADOS A UM HOSPITAL)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos", methods=["GET", "POST"])
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        nome_contato = (request.form.get("nome_contato") or "").strip()
        if not nome_contato:
            flash("Informe o nome do contato.", "error")
            return redirect(url_for("main.contatos", hospital_id=hospital_id))

        contato = Contato(
            hospital_id=hospital_id,
            hospital_nome=hospital.nome_hospital,
            nome_contato=nome_contato,
            cargo=request.form.get("cargo"),
            telefone=request.form.get("telefone"),
        )
        db.session.add(contato)
        db.session.commit()
        flash("Contato salvo!", "success")
        return redirect(url_for("main.contatos", hospital_id=hospital_id))

    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).order_by(Contato.nome_contato.asc()).all()
    return render_template("contatos.html", hospital=hospital, contatos=contatos_db)


# ======================================================
# CONTATOS (SEM ASSOCIAÇÃO - OPCIONAL)
# ======================================================
@bp.route("/contatos", methods=["GET", "POST"])
def contatos_livres():
    if request.method == "POST":
        nome_contato = (request.form.get("nome_contato") or "").strip()
        if not nome_contato:
            flash("Informe o nome do contato.", "error")
            return redirect(url_for("main.contatos_livres"))

        contato = Contato(
            hospital_id=None,
            hospital_nome=request.form.get("hospital_nome"),
            nome_contato=nome_contato,
            cargo=request.form.get("cargo"),
            telefone=request.form.get("telefone"),
        )
        db.session.add(contato)
        db.session.commit()
        flash("Contato salvo sem associação!", "success")
        return redirect(url_for("main.contatos_livres"))

    contatos_db = Contato.query.filter(Contato.hospital_id.is_(None)).order_by(Contato.nome_contato.asc()).all()
    return render_template("contatos.html", hospital=None, contatos=contatos_db)


# ======================================================
# DADOS DO HOSPITAL
# (igual ao que você mostrou, mantendo a rota)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/dados", methods=["GET", "POST"])
def dados_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()

    if request.method == "POST":
        if not dados:
            dados = DadosHospital(hospital_id=hospital_id)
            db.session.add(dados)

        # Preencha aqui com seus campos do formulário:
        dados.especialidade = request.form.get("especialidade")
        dados.leitos = request.form.get("leitos")
        dados.leitos_uti = request.form.get("leitos_uti")
        dados.fatores_decisorios = request.form.get("fatores_decisorios")
        dados.prioridades_atendimento = request.form.get("prioridades_atendimento")
        dados.certificacao = request.form.get("certificacao")
        dados.emtn = request.form.get("emtn")
        dados.emtn_membros = request.form.get("emtn_membros")
        dados.comissao_feridas = request.form.get("comissao_feridas")
        dados.comissao_feridas_membros = request.form.get("comissao_feridas_membros")
        dados.nutricao_enteral_dia = request.form.get("nutricao_enteral_dia")
        dados.pacientes_tno_dia = request.form.get("pacientes_tno_dia")
        dados.altas_orientadas = request.form.get("altas_orientadas")
        dados.quem_orienta_alta = request.form.get("quem_orienta_alta")
        dados.protocolo_evolucao_dieta = request.form.get("protocolo_evolucao_dieta")
        dados.protocolo_evolucao_dieta_qual = request.form.get("protocolo_evolucao_dieta_qual")
        dados.protocolo_lesao_pressao = request.form.get("protocolo_lesao_pressao")
        dados.protocolo_lesao_pressao_qual = request.form.get("protocolo_lesao_pressao_qual")
        dados.maior_desafio = request.form.get("maior_desafio")
        dados.dieta_padrao = request.form.get("dieta_padrao")
        dados.bomba_infusao_modelo = request.form.get("bomba_infusao_modelo")
        dados.fornecedor = request.form.get("fornecedor")
        dados.convenio_empresas = request.form.get("convenio_empresas")
        dados.reembolso = request.form.get("reembolso")
        dados.modelo_compras = request.form.get("modelo_compras")
        dados.contrato_tipo = request.form.get("contrato_tipo")
        dados.nova_etapa_negociacao = request.form.get("nova_etapa_negociacao")

        db.session.commit()
        flash("Dados do hospital salvos!", "success")
        return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))

    return render_template("dados_hospitais.html", hospital=hospital, dados=dados)


# ======================================================
# PRODUTOS DO HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/produtos", methods=["GET", "POST"])
def produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        produto = (request.form.get("produto") or "").strip()
        quantidade = request.form.get("quantidade") or "0"

        if not produto:
            flash("Informe o produto.", "error")
            return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

        try:
            qtd = int(quantidade)
        except ValueError:
            qtd = 0

        ph = ProdutoHospital(
            hospital_id=hospital_id,
            nome_hospital=hospital.nome_hospital,
            marca_planilha=request.form.get("marca_planilha"),
            produto=produto,
            quantidade=qtd,
        )
        db.session.add(ph)
        db.session.commit()
        flash("Produto salvo!", "success")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).order_by(ProdutoHospital.produto.asc()).all()
    return render_template("produtos_hospitais.html", hospital=hospital, produtos=produtos_db)


# ======================================================
# RELATÓRIOS (TELA)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/relatorios", methods=["GET"])
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


# ======================================================
# RELATÓRIO PDF
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/relatorios/pdf", methods=["GET"])
def relatorio_pdf(hospital_id):
    if build_hospital_report_pdf is None:
        flash("Função de PDF não disponível (pdf_report.py).", "error")
        return redirect(url_for("main.relatorios", hospital_id=hospital_id))

    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    pdf_bytes = build_hospital_report_pdf(hospital, contatos_db, dados, produtos_db)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"relatorio_hospital_{hospital_id}.pdf"
    )
