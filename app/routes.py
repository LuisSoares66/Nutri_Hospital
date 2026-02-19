import io
import csv
import traceback
from app.extensions import db

import os
from datetime import datetime
from flask import jsonify, request
# cache simples pra não ler o Excel toda hora
_DADOS_EXCEL_CACHE = {"mtime": None, "rows": None}

from app.excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
    load_marcas_from_produtos_excel,
    load_produtos_by_marca_from_produtos_excel,
)
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect, text

from config import Config

from app.models import Hospital, Contato, DadosHospital, ProdutoHospital, AppMeta
from app.auth import admin_required
from app.pdf_report import build_hospital_report_pdf



def _load_dados_excel_cached(data_dir="data"):
    """
    Carrega dadoshospitais.xlsx com cache por mtime.
    """
    path = os.path.join(data_dir, "dadoshospitais.xlsx")
    try:
        mtime = os.path.getmtime(path)
    except Exception:
        return []

    if _DADOS_EXCEL_CACHE["mtime"] != mtime or _DADOS_EXCEL_CACHE["rows"] is None:
        rows = load_dados_hospitais_from_excel(data_dir)  # seu loader já existe
        _DADOS_EXCEL_CACHE["rows"] = rows
        _DADOS_EXCEL_CACHE["mtime"] = mtime

    return _DADOS_EXCEL_CACHE["rows"] or []


def _pick(row: dict, candidates: list[str]) -> str:
    """
    Procura a primeira chave existente no dict (case-insensitive também).
    """
    if not row:
        return ""

    # mapa case-insensitive
    upper_map = {str(k).strip().upper(): k for k in row.keys()}
    for c in candidates:
        if c in row:
            return row.get(c) or ""
        cu = str(c).strip().upper()
        if cu in upper_map:
            return row.get(upper_map[cu]) or ""
    return ""


def _populate_dados_from_excel(dados_obj, excel_row: dict):
    """
    Mapeia o Excel dadoshospitais.xlsx (cabeçalho que você mandou) -> DadosHospital.
    Só preenche se o campo do banco estiver vazio, pra não sobrescrever edições.
    """
    if not excel_row:
        return dados_obj

    def set_if_empty(field_name: str, value: str):
        if not hasattr(dados_obj, field_name):
            return
        current = getattr(dados_obj, field_name, None)
        if current is None or str(current).strip() == "":
            setattr(dados_obj, field_name, (value or "").strip())

    # Campos principais que você já usa na tela
    set_if_empty("especialidade", _pick(excel_row, ["Qual a especialidade do hospital?", "especialidade"]))
    set_if_empty("leitos", _pick(excel_row, ["Quantos leitos?", "leitos"]))
    set_if_empty("leitos_uti", _pick(excel_row, ["Quantos leitos de UTI?", "leitos_uti"]))

    set_if_empty("fatores_decisorios", _pick(excel_row, [
        "Quais fatores são decisórios para o hospital escolher um determinado produto?",
        "fatores_decisorios"
    ]))

    set_if_empty("prioridades_atendimento", _pick(excel_row, [
        "Quais as prioridas do hospital para um atendimento nutricional de excelencia?",
        "prioridades_atendimento"
    ]))

    set_if_empty("certificacao", _pick(excel_row, [
        "O hospital tem certificação ONA, CANADIAN, Joint Comission,...)?",
        "certificacao"
    ]))

    set_if_empty("emtn", _pick(excel_row, ["O hospital tem EMTN?", "emtn"]))
    set_if_empty("emtn_membros", _pick(excel_row, ["Se sim, quais os membro (nomes e especialidade)?", "emtn_membros"]))

    # Campos adicionais (do seu Excel)
    set_if_empty("comissao_feridas", _pick(excel_row, ["Tem comissão de feridas?"]))
    set_if_empty("comissao_feridas_membros", _pick(excel_row, ["Se sim, quem faz parte?"]))

    set_if_empty("nutricao_enteral_dia", _pick(excel_row, ["Tem quantas nutrição enteral por dia?"]))
    set_if_empty("pacientes_tno_dia", _pick(excel_row, ["Tem quantos pacientes em TNO por dia?"]))

    set_if_empty("altas_orientadas", _pick(excel_row, ["Quantas altas orientadas por semana ou por mês?"]))
    set_if_empty("quem_orienta_alta", _pick(excel_row, ["Quem faz esta orientação de alta?"]))

    set_if_empty("protocolo_evolucao_dieta", _pick(excel_row, ["Existe um protocolo de evolução de dieta?"]))

    # Atenção: existe um "Qual?" genérico na planilha (logo depois do protocolo de evolução)
    set_if_empty("protocolo_evolucao_dieta_qual", _pick(excel_row, ["Qual?"]))

    set_if_empty("protocolo_lesao_pressao", _pick(excel_row, [
        "Existe um protocolo para suplementação de pacientes com lesão por pressão ou feridas?"
    ]))

    set_if_empty("maior_desafio", _pick(excel_row, [
        "Qual o maior desafio na terapia nutricional do paciente internando no hospital?"
    ]))

    set_if_empty("dieta_padrao", _pick(excel_row, ["Qual a dieta padrão utilizada no hospital?"]))

    set_if_empty("bomba_infusao_modelo", _pick(excel_row, [
        "Em relação à bomba de infusão: () é própria; () atrelada à compra de dieta; () comodato; () outro"
    ]))

    set_if_empty("fornecedor", _pick(excel_row, ["Qual fornecedor?"]))

    set_if_empty("convenio_empresas", _pick(excel_row, ["Tem convenio com empresas?"]))

    set_if_empty("convenio_empresas_modelo_pagamento", _pick(excel_row, [
        "Qual(is) e qual Modelo de pagamento (NF, brasindice com de 100%,DG)?"
    ]))

    set_if_empty("reembolso", _pick(excel_row, ["Tem reembolso?"]))

    set_if_empty("modelo_compras", _pick(excel_row, [
        "Qual modelo de compras do hospital? ()bionexo; () Contrato; () Apoio; () Cotação direta (na forma de caixa de itens)"
    ]))

    set_if_empty("contrato_tipo", _pick(excel_row, ["Se contrato, é anual ou semestral?"]))
    set_if_empty("nova_etapa_negociacao", _pick(excel_row, ["Quando será a nova etapa de negociação?"]))

    return dados_obj



def _find_dados_row_for_hospital(hospital_id: int, data_dir="data") -> dict | None:
    rows = _load_dados_excel_cached(data_dir)
    for r in rows:
        if (r.get("id_hospital") or 0) == hospital_id:
            return r
    return None





bp = Blueprint("main", __name__)

DATA_DIR = "data"
META_KEY_EXCEL_IMPORTED = "excel_import_done"


def _norm(s: str) -> str:
    return (s or "").strip().upper()


# ======================================================
# HOME
# ======================================================
@bp.route("/")
def index():
    return redirect(url_for("main.hospitais"))


@bp.route("/ping")
def ping():
    return "OK"


# ======================================================
# ADMIN
# ======================================================
@bp.route("/admin", methods=["GET"])
@admin_required
def admin_panel():
    return render_template("admin.html")


# ======================================================
# HOSPITAIS
# ======================================================
from sqlalchemy.exc import OperationalError

@bp.route("/hospitais")
def hospitais():
    try:
        hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
        return render_template("hospitais.html", hospitais=hospitais_db)
    except OperationalError as e:
        db.session.rollback()
        return (
            "Banco indisponível no momento (Render Postgres). Recarregue em 30s. "
            f"Detalhe: {e}", 503
        )



@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
    """
    Cadastra UM hospital via formulário.
    Importação por Excel é feita em /admin/importar_excel_uma_vez
    """
    if request.method == "POST":
        nome = (request.form.get("nome_hospital") or "").strip()

        if not nome:
            flash("Informe o nome do hospital.", "error")
            return redirect(url_for("main.novo_hospital"))

        h = Hospital(
            nome_hospital=nome,
            endereco=(request.form.get("endereco") or "").strip(),
            numero=(request.form.get("numero") or "").strip(),
            complemento=(request.form.get("complemento") or "").strip(),
            cep=(request.form.get("cep") or "").strip(),
            cidade=(request.form.get("cidade") or "").strip(),
            estado=(request.form.get("estado") or "").strip(),
        )

        try:
            db.session.add(h)
            db.session.commit()
            flash("Hospital cadastrado com sucesso!", "success")
            return redirect(url_for("main.hospitais"))
        except IntegrityError as e:
            db.session.rollback()
            flash("Erro de integridade ao salvar hospital (ID duplicado/constraint).", "error")
            return redirect(url_for("main.novo_hospital"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar hospital: {e}", "error")
            return redirect(url_for("main.novo_hospital"))

    return render_template("hospital_form.html")


@bp.route("/hospitais/<int:hospital_id>/info", methods=["GET", "POST"])
def hospital_info(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        nome = (request.form.get("nome_hospital") or "").strip()
        if not nome:
            flash("Nome do hospital é obrigatório.", "error")
            return redirect(url_for("main.hospital_info", hospital_id=hospital_id))

        hospital.nome_hospital = nome
        hospital.endereco = (request.form.get("endereco") or "").strip()
        hospital.numero = (request.form.get("numero") or "").strip()
        hospital.complemento = (request.form.get("complemento") or "").strip()
        hospital.cep = (request.form.get("cep") or "").strip()
        hospital.cidade = (request.form.get("cidade") or "").strip()
        hospital.estado = (request.form.get("estado") or "").strip()

        try:
            db.session.commit()
            flash("Informações do hospital atualizadas.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {e}", "error")

        return redirect(url_for("main.hospital_info", hospital_id=hospital_id))

    return render_template("hospital_info.html", hospital=hospital)


@bp.route("/hospitais/<int:hospital_id>/excluir", methods=["POST"])
@admin_required
def excluir_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    try:
        # apaga dependências na ordem (FK safe)
        Contato.query.filter_by(hospital_id=hospital_id).delete(synchronize_session=False)
        ProdutoHospital.query.filter_by(hospital_id=hospital_id).delete(synchronize_session=False)
        DadosHospital.query.filter_by(hospital_id=hospital_id).delete(synchronize_session=False)

        db.session.delete(hospital)
        db.session.commit()
        flash("Hospital apagado com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao apagar hospital: {e}", "error")

    return redirect(url_for("main.hospitais"))


# ======================================================
# CONTATOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos", methods=["GET", "POST"])
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        contato_id = request.form.get("contato_id")

        if contato_id:
            contato = Contato.query.get_or_404(contato_id)
            if contato.hospital_id != hospital_id:
                flash("Contato não pertence a este hospital.", "error")
                return redirect(url_for("main.contatos", hospital_id=hospital_id))
        else:
            contato = Contato(hospital_id=hospital_id)
            db.session.add(contato)

        contato.hospital_nome = hospital.nome_hospital
        contato.nome_contato = (request.form.get("nome_contato") or "").strip()
        contato.cargo = (request.form.get("cargo") or "").strip()
        contato.telefone = (request.form.get("telefone") or "").strip()

        db.session.commit()
        flash("Contato salvo com sucesso.", "success")
        return redirect(url_for("main.contatos", hospital_id=hospital_id))

    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).order_by(Contato.id.desc()).all()
    return render_template("contatos.html", hospital=hospital, contatos=contatos_db)


# ======================================================
# DADOS DO HOSPITAL
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/dados", methods=["GET", "POST"])
def dados_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    created_now = False



    if not dados:
        dados = DadosHospital(hospital_id=hospital_id)
        db.session.add(dados)
        db.session.commit()
        created_now = True

    # ✅ NO GET: tenta completar com dados do Excel (se ainda estiver vazio no banco)
    if request.method == "GET":
        try:
            excel_row = _find_dados_row_for_hospital(hospital_id, data_dir="data")
            if excel_row:
                _populate_dados_from_excel(dados, excel_row)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            # não trava a página — só avisa
            flash(f"Não consegui carregar dados do Excel para este hospital: {e}", "warning")

        return render_template("dados_hospitais.html", hospital=hospital, dados=dados)

    # ✅ NO POST: salva o que o usuário editou
    try:
        dados.especialidade = (request.form.get("especialidade") or "").strip()
        dados.leitos = (request.form.get("leitos") or "").strip()
        dados.leitos_uti = (request.form.get("leitos_uti") or "").strip()
        dados.fatores_decisorios = (request.form.get("fatores_decisorios") or "").strip()
        dados.prioridades_atendimento = (request.form.get("prioridades_atendimento") or "").strip()
        dados.certificacao = (request.form.get("certificacao") or "").strip()
        dados.emtn = (request.form.get("emtn") or "").strip()
        dados.emtn_membros = (request.form.get("emtn_membros") or "").strip()
        dados.comissao_feridas = (request.form.get("comissao_feridas") or "").strip()
        dados.comissao_feridas_membros = (request.form.get("comissao_feridas_membros") or "").strip()
        dados.nutricao_enteral_dia = (request.form.get("nutricao_enteral_dia") or "").strip()
        dados.pacientes_tno_dia = (request.form.get("pacientes_tno_dia") or "").strip()
        dados.altas_orientadas = (request.form.get("altas_orientadas") or "").strip()
        dados.quem_orienta_alta = (request.form.get("quem_orienta_alta") or "").strip()
        dados.protocolo_evolucao_dieta = (request.form.get("protocolo_evolucao_dieta") or "").strip()
        dados.protocolo_evolucao_dieta_qual = (request.form.get("protocolo_evolucao_dieta_qual") or "").strip()
        dados.protocolo_lesao_pressao = (request.form.get("protocolo_lesao_pressao") or "").strip()
        dados.maior_desafio = (request.form.get("maior_desafio") or "").strip()
        dados.dieta_padrao = (request.form.get("dieta_padrao") or "").strip()
        dados.bomba_infusao_modelo = (request.form.get("bomba_infusao_modelo") or "").strip()
        dados.fornecedor = (request.form.get("fornecedor") or "").strip()
        dados.convenio_empresas = (request.form.get("convenio_empresas") or "").strip()
        dados.convenio_empresas_modelo_pagamento = (request.form.get("convenio_empresas_modelo_pagamento") or "").strip()
        dados.reembolso = (request.form.get("reembolso") or "").strip()
        dados.modelo_compras = (request.form.get("modelo_compras") or "").strip()
        dados.contrato_tipo = (request.form.get("contrato_tipo") or "").strip()
        dados.nova_etapa_negociacao = (request.form.get("nova_etapa_negociacao") or "").strip()

        db.session.commit()
        flash("Dados atualizados.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao salvar dados: {e}", "error")

    return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))




# ======================================================
# PRODUTOS
# ======================================================
from flask import jsonify
import os

@bp.route("/hospitais/<int:hospital_id>/produtos", methods=["GET", "POST"])
def produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    # caminho absoluto do /data no Render
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../project/src
    data_dir = os.path.join(base_dir, "data")

    if request.method == "POST":
        try:
            produto_id_raw = (request.form.get("produto_id") or "").strip()

            if produto_id_raw:
                produto = ProdutoHospital.query.get_or_404(int(produto_id_raw))
                if produto.hospital_id != hospital_id:
                    flash("Produto não pertence a este hospital.", "error")
                    return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))
            else:
                produto = ProdutoHospital(hospital_id=hospital_id)
                db.session.add(produto)

            produto.nome_hospital = hospital.nome_hospital
            produto.marca_planilha = (request.form.get("marca_planilha") or "").strip()
            produto.produto = (request.form.get("produto") or "").strip()

            qtd_raw = (request.form.get("quantidade") or "").strip()
            try:
                produto.quantidade = int(float(qtd_raw)) if qtd_raw else 0
            except:
                produto.quantidade = 0

            db.session.commit()
            flash("Produto salvo.", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar produto: {e}", "error")

        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    # GET
    produtos_db = (
        ProdutoHospital.query
        .filter_by(hospital_id=hospital_id)
        .order_by(ProdutoHospital.id.desc())
        .all()
    )

    # ✅ marcas = abas do data/produtos.xlsx
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    marcas = load_marcas_from_produtos_excel(data_dir)

    return render_template(
        "produtos_hospitais.html",
        hospital=hospital,
        produtos=produtos_db,
        marcas_catalogo=marcas
    )


    # =======================
    # GET (tela)
    # =======================
    produtos_db = (
        ProdutoHospital.query
        .filter_by(hospital_id=hospital_id)
        .order_by(ProdutoHospital.id.desc())
        .all()
    )

    # ✅ marcas = abas do data/produtos.xlsx
    marcas = load_marcas_from_produtos_excel("data")

    return render_template(
        "produtos_hospitais.html",
        hospital=hospital,
        produtos=produtos_db,
        marcas_catalogo=marcas
    )


@bp.route("/hospitais/<int:hospital_id>/produtos/<int:produto_id>/excluir", methods=["POST"])
def excluir_produto(hospital_id, produto_id):
    p = ProdutoHospital.query.get_or_404(produto_id)
    if p.hospital_id != hospital_id:
        flash("Produto não pertence a este hospital.", "error")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    try:
        db.session.delete(p)
        db.session.commit()
        flash("Produto removido.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover produto: {e}", "error")

    return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))



@bp.route("/hospitais/<int:hospital_id>/contatos/<int:contato_id>/excluir", methods=["POST"])
def excluir_contato(hospital_id, contato_id):
    c = Contato.query.get_or_404(contato_id)
    if c.hospital_id != hospital_id:
        flash("Contato não pertence a este hospital.", "error")
        return redirect(url_for("main.contatos", hospital_id=hospital_id))

    try:
        db.session.delete(c)
        db.session.commit()
        flash("Contato removido.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover contato: {e}", "error")

    return redirect(url_for("main.contatos", hospital_id=hospital_id))



# ======================================================
# RELATÓRIOS (TELA + PDF + CSV)
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


@bp.route("/hospitais/<int:hospital_id>/relatorios/pdf")
def relatorio_pdf(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    pdf_bytes = build_hospital_report_pdf(hospital, contatos_db, dados, produtos_db)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="hospital_{hospital_id}.pdf"'}
    )


@bp.route("/relatorios")
def relatorios_geral():
    hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
    return render_template("relatorios_geral.html", hospitais=hospitais_db)


@bp.route("/relatorios/csv", methods=["POST"])
def relatorio_csv():
    hospital_id = int(request.form.get("hospital_id") or 0)
    hospital = Hospital.query.get_or_404(hospital_id)

    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    out = io.StringIO()
    w = csv.writer(out, delimiter=";")

    w.writerow(["HOSPITAL"])
    w.writerow([hospital.id, hospital.nome_hospital, hospital.cidade, hospital.estado])
    w.writerow([])

    w.writerow(["CONTATOS"])
    for c in contatos_db:
        w.writerow([c.nome_contato, c.cargo, c.telefone])
    w.writerow([])

    w.writerow(["DADOS"])
    if dados:
        w.writerow(["especialidade", dados.especialidade])
        w.writerow(["leitos", dados.leitos])
        w.writerow(["leitos_uti", dados.leitos_uti])
    w.writerow([])

    w.writerow(["PRODUTOS"])
    for p in produtos_db:
        w.writerow([p.marca_planilha, p.produto, p.quantidade])

    return Response(
        out.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="hospital_{hospital_id}.csv"'}
    )


# ======================================================
# IMPORTAÇÃO EXCEL (UMA VEZ) - COMPLETA
# ======================================================
@bp.route("/admin/importar_excel_uma_vez", methods=["POST"])
@admin_required
def importar_excel_uma_vez():
    try:
        flag = AppMeta.query.get(META_KEY_EXCEL_IMPORTED)
        if flag and (flag.value or "").lower() == "true":
            flash("Importação já foi realizada (uma vez).", "warning")
            return redirect(url_for("main.admin_panel"))

        hospitais_rows = load_hospitais_from_excel(DATA_DIR)
        contatos_rows = load_contatos_from_excel(DATA_DIR)
        dados_rows = load_dados_hospitais_from_excel(DATA_DIR)
        produtos_rows = load_produtos_hospitais_from_excel(DATA_DIR)

        if not hospitais_rows:
            flash("Nenhum hospital encontrado em data/hospitais.xlsx", "error")
            return redirect(url_for("main.admin_panel"))

        # 1) HOSPITAIS (preserva Hospital.id = id_hospital do Excel)
        importados = 0
        atualizados = 0

        for r in hospitais_rows:
            hid = r.get("id_hospital")
            nome = (r.get("nome_hospital") or "").strip()
            if not hid or not nome:
                continue

            h = Hospital.query.get(hid)
            if not h:
                h = Hospital(
                    id=hid,
                    nome_hospital=nome,
                    endereco=r.get("endereco") or "",
                    numero=r.get("numero") or "",
                    complemento=r.get("complemento") or "",
                    cep=r.get("cep") or "",
                    cidade=r.get("cidade") or "",
                    estado=r.get("estado") or "",
                )
                db.session.add(h)
                importados += 1
            else:
                h.nome_hospital = nome
                h.endereco = r.get("endereco") or ""
                h.numero = r.get("numero") or ""
                h.complemento = r.get("complemento") or ""
                h.cep = r.get("cep") or ""
                h.cidade = r.get("cidade") or ""
                h.estado = r.get("estado") or ""
                atualizados += 1

        db.session.commit()

        hospitais_existentes = {h.id for h in Hospital.query.with_entities(Hospital.id).all()}

        # 2) CONTATOS
        contatos_ok = 0
        contatos_sem = 0
        with db.session.no_autoflush:
            for r in contatos_rows:
                nome_contato = (r.get("nome_contato") or "").strip()
                if not nome_contato:
                    continue

                hid = r.get("id_hospital")
                if hid and hid not in hospitais_existentes:
                    hid = None

                c = Contato(
                    hospital_id=hid,
                    hospital_nome=(r.get("hospital_nome") or "").strip(),
                    nome_contato=nome_contato,
                    cargo=r.get("cargo") or "",
                    telefone=r.get("telefone") or "",
                )
                db.session.add(c)
                if hid is None:
                    contatos_sem += 1
                else:
                    contatos_ok += 1

        db.session.commit()

        # 3) DADOS
        dados_new = 0
        dados_upd = 0
        dados_skip = 0

        for r in dados_rows:
            hid = r.get("id_hospital")
            if not hid or hid not in hospitais_existentes:
                dados_skip += 1
                continue

            d = DadosHospital.query.filter_by(hospital_id=hid).first()
            if not d:
                d = DadosHospital(hospital_id=hid)
                db.session.add(d)
                dados_new += 1
            else:
                dados_upd += 1

            d.especialidade = r.get("especialidade") or r.get("Qual a especialidade do hospital?") or ""
            d.leitos = r.get("leitos") or r.get("Quantos leitos?") or ""
            d.leitos_uti = r.get("leitos_uti") or r.get("Quantos leitos de UTI?") or ""
            d.fatores_decisorios = r.get("fatores_decisorios") or ""
            d.prioridades_atendimento = r.get("prioridades_atendimento") or ""
            d.certificacao = r.get("certificacao") or ""
            d.emtn = r.get("emtn") or ""
            d.emtn_membros = r.get("emtn_membros") or ""

        db.session.commit()

        # 4) PRODUTOS
        prod_ok = 0
        prod_skip = 0

        for r in produtos_rows:
            hid = r.get("hospital_id") or r.get("id_hospital")
            if not hid or hid not in hospitais_existentes:
                prod_skip += 1
                continue

            produto_nome = (r.get("produto") or "").strip()
            if not produto_nome:
                continue

            try:
                qtd = int(r.get("quantidade") or 0)
            except:
                qtd = 0

            p = ProdutoHospital(
                hospital_id=hid,
                nome_hospital=r.get("nome_hospital") or "",
                marca_planilha=r.get("marca_planilha") or "",
                produto=produto_nome,
                quantidade=qtd,
            )
            db.session.add(p)
            prod_ok += 1

        db.session.commit()

        # 5) Marca como feito
        if not flag:
            flag = AppMeta(key=META_KEY_EXCEL_IMPORTED, value="true")
            db.session.add(flag)
        else:
            flag.value = "true"
        db.session.commit()

        flash(
            f"Importação concluída ✅ "
            f"Hospitais +{importados} / atualizados {atualizados} | "
            f"Contatos associados {contatos_ok} / sem hospital {contatos_sem} | "
            f"Dados +{dados_new} / atualizados {dados_upd} / ignorados {dados_skip} | "
            f"Produtos +{prod_ok} / ignorados {prod_skip}.",
            "success"
        )
        return redirect(url_for("main.hospitais"))

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao importar: {e}", "error")
        return redirect(url_for("main.admin_panel"))


# ======================================================
# RESET COMPLETO DO BANCO (SOMENTE ADMIN)
# ======================================================
@bp.route("/admin/reset_db", methods=["POST"])
@admin_required
def reset_db():
    reset_password = request.form.get("reset_password")
    confirm_text = request.form.get("confirm_text")

    admin_pass = os.environ.get("ADMIN_PASS", "")  # pega direto do Render

    if not admin_pass:
        flash("ADMIN_PASS não encontrada nas variáveis de ambiente do Render.", "error")
        return redirect(url_for("main.admin_panel"))

    if reset_password != admin_pass:
        flash("Senha inválida.", "error")
        return redirect(url_for("main.admin_panel"))

    if confirm_text != "APAGAR":
        flash("Confirmação inválida. Digite exatamente APAGAR.", "error")
        return redirect(url_for("main.admin_panel"))

    try:
        AppMeta.query.delete()
        Contato.query.delete()
        ProdutoHospital.query.delete()
        DadosHospital.query.delete()
        Hospital.query.delete()
        db.session.commit()

        flash("Banco de dados zerado com sucesso.", "success")
        return redirect(url_for("main.hospitais"))

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao zerar banco: {e}", "error")
        return redirect(url_for("main.admin_panel"))


from sqlalchemy import text

@bp.route("/admin/fix_schema_dados", methods=["POST"])
@admin_required
def fix_schema_dados():
    try:
        # adiciona colunas caso não existam (Postgres)
        stmts = [
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS comissao_feridas TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS comissao_feridas_membros TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS nutricao_enteral_dia TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS pacientes_tno_dia TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS altas_orientadas TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS quem_orienta_alta TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS protocolo_evolucao_dieta TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS protocolo_evolucao_dieta_qual TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS protocolo_lesao_pressao TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS maior_desafio TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS dieta_padrao TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS bomba_infusao_modelo TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS fornecedor TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS convenio_empresas TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS convenio_empresas_modelo_pagamento TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS reembolso TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS modelo_compras TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS contrato_tipo TEXT DEFAULT '';",
            "ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS nova_etapa_negociacao TEXT DEFAULT '';",
        ]
        for s in stmts:
            db.session.execute(text(s))

        db.session.commit()
        flash("Schema corrigido: colunas de dados_hospitais criadas/garantidas ✅", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao corrigir schema: {e}", "error")

    return redirect(url_for("main.admin_panel"))



@bp.route("/api/catalogo_produtos", methods=["GET"], endpoint="catalogo_produtos")
def api_catalogo_produtos():
    marca = (request.args.get("marca") or "").strip()
    if not marca:
        return jsonify({"marca": "", "produtos": []})

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    produtos = load_produtos_by_marca_from_produtos_excel(marca, data_dir)
    return jsonify({"marca": marca, "produtos": produtos})

@bp.route("/hospitais/<int:hospital_id>/produtos/editar", methods=["GET"])
def editar_produtos_hospital(hospital_id):
    return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))









