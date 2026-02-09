import os
import io

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, send_file
)
from sqlalchemy import inspect, text

from app import db
from app.auth import admin_required
from app.models import Hospital, Contato, DadosHospital, ProdutoHospital, AppMeta
from app.excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
)
from app.pdf_report import build_hospital_report_pdf


bp = Blueprint("main", __name__)

# pasta /data na raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


# ======================================================
# HOME
# ======================================================
@bp.route("/")
def index():
    return redirect(url_for("main.hospitais"))


# ======================================================
# PAINEL ADMIN (para evitar popup em todo clique)
# ======================================================
@bp.route("/admin", methods=["GET"])
@admin_required
def admin_panel():
    return render_template("admin.html")


# ======================================================
# LISTA DE HOSPITAIS
# ======================================================
@bp.route("/hospitais", methods=["GET"])
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
            nome_hospital=(request.form.get("nome_hospital") or "").strip(),
            endereco=(request.form.get("endereco") or "").strip(),
            numero=(request.form.get("numero") or "").strip(),
            complemento=(request.form.get("complemento") or "").strip(),
            cep=(request.form.get("cep") or "").strip(),
            cidade=(request.form.get("cidade") or "").strip(),
            estado=(request.form.get("estado") or "").strip(),
        )
        if not h.nome_hospital:
            flash("Informe o nome do hospital.", "error")
            return render_template("hospital_form.html", hospital=None)

        db.session.add(h)
        db.session.commit()
        flash("Hospital cadastrado com sucesso!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html", hospital=None)


# ======================================================
# APAGAR HOSPITAL (apaga tudo relacionado via cascade)
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
@bp.route("/hospitais/<int:hospital_id>/contatos", methods=["GET"])
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
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

        # atualiza somente campos que existirem no model
        for field, value in request.form.items():
            if hasattr(dados, field):
                setattr(dados, field, value)

        db.session.commit()
        flash("Dados salvos com sucesso.", "success")
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
        marca = (request.form.get("marca_planilha") or "").strip()
        qtd_raw = (request.form.get("quantidade") or "0").strip()

        if not produto:
            flash("Informe o produto.", "error")
            return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

        try:
            quantidade = int(float(qtd_raw.replace(",", "."))) if qtd_raw else 0
        except ValueError:
            quantidade = 0

        novo = ProdutoHospital(
            hospital_id=hospital_id,
            nome_hospital=hospital.nome_hospital,
            marca_planilha=marca,
            produto=produto,
            quantidade=quantidade,
        )
        db.session.add(novo)
        db.session.commit()
        flash("Produto adicionado com sucesso!", "success")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    produtos_db = (
        ProdutoHospital.query
        .filter_by(hospital_id=hospital_id)
        .order_by(ProdutoHospital.produto.asc())
        .all()
    )

    return render_template("produtos_hospitais.html", hospital=hospital, produtos=produtos_db)


# ======================================================
# RELATÓRIOS (visão completa)
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
        produtos=produtos_db
    )


# ======================================================
# RELATÓRIO PDF
# ======================================================
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
        download_name=f"relatorio_hospital_{hospital_id}.pdf"
    )


# ======================================================
# IMPORTAR EXCEL (UMA VEZ) - IMPORTA TUDO
# ======================================================
@bp.route("/admin/importar_excel_uma_vez", methods=["POST"])
@admin_required
def importar_excel_uma_vez():
    done = AppMeta.query.filter_by(key="excel_import_done").first()
    if done:
        flash("Importação BLOQUEADA: já foi importado uma vez.", "warning")
        return redirect(url_for("main.hospitais"))

    def _norm(v):
        return str(v).strip() if v is not None else ""

    def _to_int(v):
        s = _norm(v)
        if not s:
            return None
        try:
            return int(float(s.replace(",", ".")))
        except Exception:
            return None

    def _find_hospital_id(row: dict):
        hid = _to_int(row.get("id_hospital")) or _to_int(row.get("hospital_id")) or _to_int(row.get("hospital_id"))
        if hid and Hospital.query.get(hid):
            return hid

        nome = _norm(row.get("nome_hospital") or row.get("hospital_nome"))
        if nome:
            h = Hospital.query.filter_by(nome_hospital=nome).first()
            if h:
                return h.id
        return None

    # 1) HOSPITAIS
    for r in load_hospitais_from_excel(DATA_DIR):
        if not isinstance(r, dict):
            continue

        nome = _norm(r.get("nome_hospital"))
        if not nome:
            continue

        if Hospital.query.filter_by(nome_hospital=nome).first():
            continue

        hid = _to_int(r.get("id_hospital"))

        h = Hospital(
            nome_hospital=nome,
            endereco=_norm(r.get("endereco")),
            numero=_norm(r.get("numero")),
            complemento=_norm(r.get("complemento")),
            cep=_norm(r.get("cep")),
            cidade=_norm(r.get("cidade")),
            estado=_norm(r.get("estado")),
        )
        if hid and not Hospital.query.get(hid):
            h.id = hid

        db.session.add(h)

    db.session.commit()

    # 2) CONTATOS (permite hospital_id None)
    for r in load_contatos_from_excel(DATA_DIR):
        if not isinstance(r, dict):
            continue

        nome_contato = _norm(r.get("nome_contato"))
        if not nome_contato:
            continue

        hospital_id = _find_hospital_id(r)  # pode ser None
        hospital_nome = _norm(r.get("hospital_nome") or r.get("nome_hospital"))
        telefone = _norm(r.get("telefone"))
        cargo = _norm(r.get("cargo"))

        # evita duplicar
        existe = Contato.query.filter_by(
            hospital_id=hospital_id,
            nome_contato=nome_contato,
            telefone=telefone
        ).first()
        if existe:
            continue

        c = Contato(
            hospital_id=hospital_id,
            hospital_nome=hospital_nome,
            nome_contato=nome_contato,
            cargo=cargo,
            telefone=telefone
        )
        cid = _to_int(r.get("id_contato"))
        if cid and not Contato.query.get(cid):
            c.id = cid

        db.session.add(c)

    db.session.commit()

    # 3) DADOS HOSPITAIS (1 por hospital)
    for r in load_dados_hospitais_from_excel(DATA_DIR):
        if not isinstance(r, dict):
            continue

        hospital_id = _find_hospital_id(r)
        if not hospital_id:
            continue

        dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
        if not dados:
            dados = DadosHospital(hospital_id=hospital_id)
            db.session.add(dados)

        # mapeamento pelas PERGUNTAS do Excel
        dados.especialidade = _norm(r.get("Qual a especialidade do hospital?"))
        dados.leitos = _norm(r.get("Quantos leitos?"))
        dados.leitos_uti = _norm(r.get("Quantos leitos de UTI?"))
        dados.fatores_decisorios = _norm(r.get("Quais fatores são decisórios para o hospital escolher um determinado produto?"))
        dados.prioridades_atendimento = _norm(r.get("Quais as prioridas do hospital para um atendimento nutricional de excelencia?"))
        dados.certificacao = _norm(r.get("O hospital tem certificação ONA, CANADIAN, Joint Comission,...)?"))
        dados.emtn = _norm(r.get("O hospital tem EMTN?"))
        dados.emtn_membros = _norm(r.get("Se sim, quais os membro (nomes e especialidade)?"))
        dados.comissao_feridas = _norm(r.get("Tem comissão de feridas?"))
        dados.comissao_feridas_membros = _norm(r.get("Se sim, quem faz parte?"))
        dados.nutricao_enteral_dia = _norm(r.get("Tem quantas nutrição enteral por dia?"))
        dados.pacientes_tno_dia = _norm(r.get("Tem quantos pacientes em TNO por dia?"))
        dados.altas_orientadas = _norm(r.get("Quantas altas orientadas por semana ou por mês?"))
        dados.quem_orienta_alta = _norm(r.get("Quem faz esta orientação de alta?"))
        dados.protocolo_evolucao_dieta = _norm(r.get("Existe um protocolo de evolução de dieta?"))
        dados.protocolo_evolucao_dieta_qual = _norm(r.get("Qual?"))
        dados.protocolo_lesao_pressao = _norm(r.get("Existe um protocolo para suplementação de pacientes com lesão por pressão ou feridas?"))
        dados.protocolo_lesao_pressao_qual = _norm(r.get("Qual o maior desafio na terapia nutricional do paciente internando no hospital?"))
        dados.dieta_padrao = _norm(r.get("Qual a dieta padrão utilizada no hospital?"))
        dados.bomba_infusao_modelo = _norm(r.get("Em relação à bomba de infusão: () é própria; () atrelada à compra de dieta; () comodato; () outro"))
        dados.fornecedor = _norm(r.get("Qual fornecedor?"))
        dados.convenio_empresas = _norm(r.get("Tem convenio com empresas?"))
        dados.reembolso = _norm(r.get("Tem reembolso?"))
        dados.modelo_compras = _norm(r.get("Qual modelo de compras do hospital? ()bionexo; () Contrato; () Apoio; () Cotação direta (na forma de caixa de itens)"))
        dados.contrato_tipo = _norm(r.get("Se contrato, é anual ou semestral?"))
        dados.nova_etapa_negociacao = _norm(r.get("Quando será a nova etapa de negociação?"))

    db.session.commit()

    # 4) PRODUTOS HOSPITAIS
    for r in load_produtos_hospitais_from_excel(DATA_DIR):
        if not isinstance(r, dict):
            continue

        hospital_id = _find_hospital_id(r)
        if not hospital_id:
            continue

        produto = _norm(r.get("produto"))
        if not produto:
            continue

        qtd = _to_int(r.get("quantidade")) or 0
        nome_hospital = _norm(r.get("nome_hospital"))
        marca = _norm(r.get("marca_planilha"))

        # evita duplicar (hospital + produto)
        existe = ProdutoHospital.query.filter_by(hospital_id=hospital_id, produto=produto).first()
        if existe:
            continue

        db.session.add(ProdutoHospital(
            hospital_id=hospital_id,
            nome_hospital=nome_hospital,
            marca_planilha=marca,
            produto=produto,
            quantidade=qtd
        ))

    db.session.commit()

    # trava importação
    db.session.add(AppMeta(key="excel_import_done", value="1"))
    db.session.commit()

    flash("Importação OK: Hospitais + Contatos + Dados + Produtos.", "success")
    return redirect(url_for("main.hospitais"))


# ======================================================
# RESET TOTAL DO BANCO (TRUNCATE)
# ======================================================
@bp.route("/admin/reset_db", methods=["POST"])
@admin_required
def reset_db():
    reset_pass = (os.getenv("RESET_DB_PASSWORD") or "").strip()
    typed = (request.form.get("reset_password") or "").strip()
    confirm = (request.form.get("confirm_text") or "").strip().upper()

    if not reset_pass:
        flash("RESET_DB_PASSWORD não configurada no Render.", "error")
        return redirect(url_for("main.admin_panel"))

    if typed != reset_pass:
        flash("Senha reset incorreta.", "error")
        return redirect(url_for("main.admin_panel"))

    if confirm != "APAGAR":
        flash("Confirmação inválida. Digite APAGAR.", "error")
        return redirect(url_for("main.admin_panel"))

    insp = inspect(db.engine)
    tables = insp.get_table_names()

    protected = {"alembic_version", "app_meta"}

    try:
        with db.engine.begin() as conn:
            for t in tables:
                if t not in protected:
                    conn.execute(text(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE;'))

        # libera importação novamente
        AppMeta.query.delete()
        db.session.commit()

        flash("Banco zerado com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao zerar banco: {e}", "error")

    return redirect(url_for("main.admin_panel"))
