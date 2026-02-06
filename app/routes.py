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

from sqlalchemy import text

@bp.route("/admin/importar_tudo_excel_uma_vez", methods=["GET"])
@admin_required
def importar_tudo_excel_uma_vez():
    """
    Importa TODOS os dados (hospitais + contatos + dadoshospitais + produtoshospitais)
    SOMENTE se o banco estiver vazio.
    """
    # 1) Bloqueio: só roda se estiver "zerado"
    if Hospital.query.first() is not None:
        return "Importação BLOQUEADA: já existem hospitais no banco. (Roda apenas uma vez)", 400

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    # ============
    # HOSPITAIS
    # ============
    hospitais_rows = load_hospitais_from_excel(data_dir)

    # Mapeia id do excel -> id do banco (vamos tentar manter o id do excel se vier preenchido)
    excel_to_db = {}
    criados_hosp = 0

    for r in hospitais_rows:
        nome = (r.get("nome_hospital") or "").strip()
        if not nome:
            continue

        # tenta pegar id_hospital do excel
        raw_id = str(r.get("id_hospital") or "").strip()
        excel_id = None
        if raw_id.isdigit():
            excel_id = int(raw_id)

        h = Hospital(
            nome_hospital=nome,
            endereco=r.get("endereco") or "",
            numero=str(r.get("numero") or ""),
            complemento=r.get("complemento") or "",
            cep=str(r.get("cep") or ""),
            cidade=r.get("cidade") or "",
            estado=r.get("estado") or "",
        )

        # se o excel tiver id_hospital numérico, usamos como id do banco
        if excel_id is not None:
            h.id = excel_id

        db.session.add(h)
        criados_hosp += 1

    db.session.commit()

    # cria mapeamento após commit
    for h in Hospital.query.all():
        excel_to_db[h.id] = h.id  # como mantivemos ids, fica 1:1

    # Ajusta a sequence do Postgres para continuar depois do maior id
    # (evita erro ao criar novos hospitais após a importação)
    db.session.execute(
        text("SELECT setval(pg_get_serial_sequence('hospitais','id'), COALESCE(MAX(id), 1)) FROM hospitais;")
    )
    db.session.commit()

    # ============
    # CONTATOS
    # ============
    contatos_rows = load_contatos_from_excel(data_dir)
    criados_cont = 0

    for r in contatos_rows:
        nome_contato = (r.get("nome_contato") or "").strip()
        if not nome_contato:
            continue

        raw_hid = str(r.get("id_hospital") or "").strip()
        hospital_id = int(raw_hid) if raw_hid.isdigit() else None

        # pode salvar sem associação (hospital_id=None)
        if hospital_id is not None and hospital_id not in excel_to_db:
            hospital_id = None

        telefone = (r.get("telefone") or "").strip()

        # evita duplicar grosso modo (nome + telefone + hospital)
        existe = Contato.query.filter_by(
            hospital_id=hospital_id,
            nome_contato=nome_contato,
            telefone=telefone
        ).first()
        if existe:
            continue

        c = Contato(
            hospital_id=hospital_id,
            hospital_nome=(r.get("hospital_nome") or "").strip(),
            nome_contato=nome_contato,
            cargo=(r.get("cargo") or "").strip(),
            telefone=telefone,
        )
        db.session.add(c)
        criados_cont += 1

    db.session.commit()

    # ============
    # DADOS HOSPITAIS
    # ============
    dados_rows = load_dados_hospitais_from_excel(data_dir)
    criados_dados = 0

    for r in dados_rows:
        raw_hid = str(r.get("id_hospital") or "").strip()
        if not raw_hid.isdigit():
            continue
        hid = int(raw_hid)
        if hid not in excel_to_db:
            continue

        dados = DadosHospital.query.filter_by(hospital_id=hid).first()
        if not dados:
            dados = DadosHospital(hospital_id=hid)
            db.session.add(dados)
            criados_dados += 1

        # mapeamento (principais campos + você pode completar depois)
        dados.especialidade = r.get("Qual a especialidade do hospital?")
        dados.leitos = str(r.get("Quantos leitos?") or "")
        dados.leitos_uti = str(r.get("Quantos leitos de UTI?") or "")
        dados.fatores_decisorios = r.get("Quais fatores são decisórios para o hospital escolher um determinado produto?")
        dados.prioridades_atendimento = r.get("Quais as prioridas do hospital para um atendimento nutricional de excelencia?")
        dados.certificacao = r.get("O hospital tem certificação ONA, CANADIAN, Joint Comission,...)?")
        dados.emtn = r.get("O hospital tem EMTN?")
        dados.emtn_membros = r.get("Se sim, quais os membro (nomes e especialidade)?")
        dados.comissao_feridas = r.get("Tem comissão de feridas?")
        dados.comissao_feridas_membros = r.get("Se sim, quem faz parte?")
        dados.nutricao_enteral_dia = str(r.get("Tem quantas nutrição enteral por dia?") or "")
        dados.pacientes_tno_dia = str(r.get("Tem quantos pacientes em TNO por dia?") or "")
        dados.altas_orientadas = str(r.get("Quantas altas orientadas por semana ou por mês?") or "")
        dados.quem_orienta_alta = r.get("Quem faz esta orientação de alta?")
        dados.protocolo_evolucao_dieta = r.get("Existe um protocolo de evolução de dieta?")
        dados.protocolo_evolucao_dieta_qual = r.get("Qual?")
        dados.protocolo_lesao_pressao = r.get("Existe um protocolo para suplementação de pacientes com lesão por pressão ou feridas?")
        dados.protocolo_lesao_pressao_qual = r.get("Qual o maior desafio na terapia nutricional do paciente internando no hospital?")
        dados.dieta_padrao = r.get("Qual a dieta padrão utilizada no hospital?")
        dados.bomba_infusao_modelo = r.get("Em relação à bomba de infusão: () é própria; () atrelada à compra de dieta; () comodato; () outro")
        dados.fornecedor = r.get("Qual fornecedor?")
        dados.convenio_empresas = r.get("Tem convenio com empresas?")
        dados.reembolso = r.get("Tem reembolso?")
        dados.modelo_compras = r.get("Qual modelo de compras do hospital? ()bionexo; () Contrato; () Apoio; () Cotação direta (na forma de caixa de itens)")
        dados.contrato_tipo = r.get("Se contrato, é anual ou semestral?")
        dados.nova_etapa_negociacao = r.get("Quando será a nova etapa de negociação?")

    db.session.commit()

    # ============
    # PRODUTOS HOSPITAIS
    # ============
    prod_rows = load_produtos_hospitais_from_excel(data_dir)
    criados_prod = 0

    for r in prod_rows:
        raw_hid = str(r.get("hospital_id") or r.get("id_hospital") or "").strip()
        if not raw_hid.isdigit():
            continue
        hid = int(raw_hid)
        if hid not in excel_to_db:
            continue

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

        ph = ProdutoHospital(
            hospital_id=hid,
            nome_hospital=(r.get("nome_hospital") or "").strip(),
            produto=produto,
            quantidade=qtd,
            marca_planilha=(r.get("marca_planilha") or "").strip(),
        )
        db.session.add(ph)
        criados_prod += 1

    db.session.commit()

    return (
        f"IMPORTAÇÃO OK (UMA VEZ): "
        f"Hospitais={criados_hosp}, Contatos={criados_cont}, "
        f"DadosHospitais={criados_dados}, Produtos={criados_prod}"
    )
