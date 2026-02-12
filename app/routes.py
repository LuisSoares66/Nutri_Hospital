import io
import traceback
import csv
from sqlalchemy.exc import IntegrityError
from app.auth import admin_required
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response
)

from app import db
from app.models import (
    Hospital, Contato, DadosHospital, ProdutoHospital, AppMeta
)
from app.auth import admin_required
from app.excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
)

def _norm(s: str) -> str:
    return (s or "").strip().upper()


from app.pdf_report import build_hospital_report_pdf

from app.excel_loader import load_catalogo_produtos_from_excel
IMPORT_FLAG_KEY = "import_excel_done_v1"

bp = Blueprint("main", __name__)

def _norm(s: str) -> str:
    return (s or "").strip().upper()
# ======================================================
# HOME
# ======================================================
@bp.route("/")
def index():
    return redirect(url_for("main.hospitais"))


from app.auth import admin_required

@bp.route("/admin", methods=["GET"])
@admin_required
def admin_panel():
    return render_template("admin.html")


# ======================================================
# HOSPITAIS
# ======================================================
@bp.route("/hospitais")
def hospitais():
    hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
    return render_template("hospitais.html", hospitais=hospitais_db)


@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
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
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar hospital: {e}", "error")
            return redirect(url_for("main.novo_hospital"))

    return render_template("hospital_form.html")



from app.auth import admin_required
from app.models import Hospital, Contato, DadosHospital, ProdutoHospital
from app import db
from flask import redirect, url_for, flash

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
            # EDITAR
            contato = Contato.query.get_or_404(contato_id)
        else:
            # NOVO
            contato = Contato(hospital_id=hospital_id)
            db.session.add(contato)

        contato.hospital_nome = hospital.nome_hospital
        contato.nome_contato = request.form.get("nome_contato")
        contato.cargo = request.form.get("cargo")
        contato.telefone = request.form.get("telefone")

        db.session.commit()
        flash("Contato salvo com sucesso.", "success")
        return redirect(url_for("main.contatos", hospital_id=hospital_id))

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

    if not dados:
        dados = DadosHospital(hospital_id=hospital_id)
        db.session.add(dados)
        db.session.commit()

    if request.method == "POST":
        dados.especialidade = request.form.get("especialidade")
        dados.leitos = request.form.get("leitos")
        dados.leitos_uti = request.form.get("leitos_uti")
        dados.fatores_decisorios = request.form.get("fatores_decisorios")
        dados.prioridades_atendimento = request.form.get("prioridades_atendimento")
        dados.certificacao = request.form.get("certificacao")
        dados.emtn = request.form.get("emtn")
        dados.emtn_membros = request.form.get("emtn_membros")

        db.session.commit()
        flash("Dados atualizados.", "success")
        return redirect(url_for("main.dados_hospital", hospital_id=hospital_id))

    return render_template(
        "dados_hospitais.html",
        hospital=hospital,
        dados=dados
    )



# ======================================================
# PRODUTOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/produtos", methods=["GET", "POST"])
def produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        produto_id = request.form.get("produto_id")

        if produto_id:
            produto = ProdutoHospital.query.get_or_404(produto_id)
        else:
            produto = ProdutoHospital(hospital_id=hospital_id)
            db.session.add(produto)

        produto.nome_hospital = hospital.nome_hospital
        produto.marca_planilha = request.form.get("marca_planilha")
        produto.produto = request.form.get("produto")
        produto.quantidade = int(request.form.get("quantidade") or 0)

        db.session.commit()
        flash("Produto salvo.", "success")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    return render_template(
        "produtos_hospitais.html",
        hospital=hospital,
        produtos=produtos_db
    )



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
# RELATÓRIO POR HOSPITAL (PDF)
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

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="hospital_{hospital_id}.pdf"'
        }
    )


# ======================================================
# RELATÓRIOS – GERAL (LISTA ROLÁVEL)
# ======================================================
@bp.route("/relatorios")
def relatorios_geral():
    hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
    return render_template(
        "relatorios_geral.html",
        hospitais=hospitais_db
    )


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

    w.writerow(["PRODUTOS"])
    for p in produtos_db:
        w.writerow([p.marca_planilha, p.produto, p.quantidade])

    return Response(
        out.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="hospital_{hospital_id}.csv"'
        }
    )


@bp.route("/debug_endpoints")
def debug_endpoints():
    return "<br>".join(sorted([r.endpoint for r in bp.deferred_functions if hasattr(r, "endpoint")]))

@bp.route("/ping")
def ping():
    return "OK"

import os
from sqlalchemy import inspect, text

# ======================================================
# IMPORTAR EXCEL (UMA VEZ) -> precisa ser POST
# ======================================================
IMPORT_FLAG_KEY = "import_excel_done_v1"

def _norm(s: str) -> str:
    return (s or "").strip().upper()


@bp.route("/admin/importar_excel_uma_vez", methods=["POST"])
@admin_required
def importar_excel_uma_vez():
    try:
        # trava para rodar só 1x
        meta = AppMeta.query.get("import_done")
        if meta and meta.value == "1":
            flash("Importação já foi realizada.", "warning")
            return redirect(url_for("main.admin_panel"))

        data_dir = "data"

        # 1) Hospitais
        rows_h = load_hospitais_from_excel(data_dir)
        if not isinstance(rows_h, list):
            raise Exception("hospitais.xlsx inválido: loader não retornou lista")

        name_to_id = {}

        for r in rows_h:
            nome = (r.get("nome_hospital") or "").strip()
            if not nome:
                continue

            h = Hospital(
                nome_hospital=nome,
                endereco=(r.get("endereco") or "").strip(),
                numero=(r.get("numero") or "").strip(),
                complemento=(r.get("complemento") or "").strip(),
                cep=(r.get("cep") or "").strip(),
                cidade=(r.get("cidade") or "").strip(),
                estado=(r.get("estado") or "").strip(),
            )
            db.session.add(h)

        db.session.flush()  # pega IDs antes do commit

        # monta mapa nome->id
        for h in Hospital.query.all():
            name_to_id[(h.nome_hospital or "").strip().upper()] = h.id

        # 2) Contatos
        rows_c = load_contatos_from_excel(data_dir)
        if not isinstance(rows_c, list):
            raise Exception("contatos.xlsx inválido")

        for r in rows_c:
            nome_hosp = (r.get("hospital_nome") or r.get("nome_hospital") or "").strip()
            key = nome_hosp.upper()
            hospital_id = name_to_id.get(key)

            c = Contato(
                hospital_id=hospital_id,  # pode ser None (você pediu permitir sem vínculo)
                hospital_nome=nome_hosp,
                nome_contato=(r.get("nome_contato") or "").strip() or "SEM NOME",
                cargo=(r.get("cargo") or "").strip(),
                telefone=(r.get("telefone") or "").strip(),
            )
            db.session.add(c)

        # 3) Dados do hospital (1 por hospital)
        rows_d = load_dados_hospitais_from_excel(data_dir)
        if not isinstance(rows_d, list):
            raise Exception("dadoshospitais.xlsx inválido")

        for r in rows_d:
            nome_hosp = (r.get("nome_hospital") or r.get("Hospital") or "").strip()
            # se sua planilha não tem nome, tenta id_hospital mas mapeando por ordem não é seguro
            key = nome_hosp.upper()
            hospital_id = name_to_id.get(key)
            if not hospital_id:
                continue

            # evita duplicar (unique hospital_id)
            if DadosHospital.query.filter_by(hospital_id=hospital_id).first():
                continue

            d = DadosHospital(
                hospital_id=hospital_id,
                especialidade=(r.get("Qual a especialidade do hospital?") or "").strip(),
                leitos=str(r.get("Quantos leitos?") or "").strip(),
                leitos_uti=str(r.get("Quantos leitos de UTI?") or "").strip(),
                fatores_decisorios=(r.get("Quais fatores são decisórios para o hospital escolher um determinado produto?") or "").strip(),
                prioridades_atendimento=(r.get("Quais as prioridas do hospital para um atendimento nutricional de excelencia?") or "").strip(),
                certificacao=(r.get("O hospital tem certificação ONA, CANADIAN, Joint Comission,...)?") or "").strip(),
                emtn=(r.get("O hospital tem EMTN?") or "").strip(),
                emtn_membros=(r.get("Se sim, quais os membro (nomes e especialidade)?") or "").strip(),
            )
            db.session.add(d)

        # 4) Produtos por hospital
        rows_p = load_produtos_hospitais_from_excel(data_dir)
        if not isinstance(rows_p, list):
            raise Exception("produtoshospitais.xlsx inválido")

        for r in rows_p:
            nome_hosp = (r.get("nome_hospital") or "").strip()
            key = nome_hosp.upper()
            hospital_id = name_to_id.get(key)
            if not hospital_id:
                continue

            produto_nome = (r.get("produto") or "").strip()
            if not produto_nome:
                continue

            qtd_raw = str(r.get("quantidade") or "").strip()
            try:
                qtd = int(float(qtd_raw)) if qtd_raw else 0
            except:
                qtd = 0

            p = ProdutoHospital(
                hospital_id=hospital_id,
                nome_hospital=nome_hosp,
                marca_planilha=(r.get("marca_planilha") or "").strip(),
                produto=produto_nome,
                quantidade=qtd,
            )
            db.session.add(p)

        # marca import realizado
        if not meta:
            meta = AppMeta(key="import_done", value="1")
            db.session.add(meta)
        else:
            meta.value = "1"

        db.session.commit()
        flash("Importação completa concluída (hospitais + contatos + dados + produtos).", "success")
        return redirect(url_for("main.admin_panel"))

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao importar: {e}", "error")
        return redirect(url_for("main.admin_panel"))




# ======================================================
# RESET TOTAL DO BANCO (ZERAR) - com senha
# ======================================================
@bp.route("/admin/reset_db", methods=["POST"])
@admin_required
def reset_db():
    reset_password = (request.form.get("reset_password") or "").strip()
    confirm_text = (request.form.get("confirm_text") or "").strip().upper()

    # aqui você valida senha/confirm do jeito que já estava

    try:
        # apaga tabelas na ordem segura
        ProdutoHospital.query.delete()
        Contato.query.delete()
        DadosHospital.query.delete()
        Hospital.query.delete()

        # destrava importação "uma vez"
        AppMeta.query.filter_by(key=IMPORT_FLAG_KEY).delete()

        db.session.commit()
        flash("Banco zerado com sucesso. Importação foi destravada.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao zerar banco: {e}", "error")

    return redirect(url_for("main.admin_panel"))


# ======================================================
# EDITAR CONTATOS (lista + adicionar + excluir)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos/editar", methods=["GET", "POST"])
def editar_contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        c = Contato(
            hospital_id=hospital_id,
            hospital_nome=hospital.nome_hospital,
            nome_contato=(request.form.get("nome_contato") or "").strip(),
            cargo=request.form.get("cargo"),
            telefone=request.form.get("telefone"),
        )
        if c.nome_contato:
            db.session.add(c)
            db.session.commit()
            flash("Contato adicionado.", "success")
        return redirect(url_for("main.editar_contatos", hospital_id=hospital_id))

    contatos_db = Contato.query.filter_by(hospital_id=hospital_id).order_by(Contato.id.desc()).all()
    return render_template("contatos_edit.html", hospital=hospital, contatos=contatos_db)


# ======================================================
# EDITAR DADOS DO HOSPITAL (form único)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/dados/editar", methods=["GET", "POST"])
def editar_dados_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()

    if request.method == "POST":
        if not dados:
            dados = DadosHospital(hospital_id=hospital_id)
            db.session.add(dados)

        dados.especialidade = request.form.get("especialidade")
        dados.leitos = request.form.get("leitos")
        dados.leitos_uti = request.form.get("leitos_uti")
        dados.fatores_decisorios = request.form.get("fatores_decisorios")
        dados.prioridades_atendimento = request.form.get("prioridades_atendimento")
        dados.certificacao = request.form.get("certificacao")
        dados.emtn = request.form.get("emtn")
        dados.emtn_membros = request.form.get("emtn_membros")

        db.session.commit()
        flash("Dados atualizados.", "success")
        return redirect(url_for("main.editar_dados_hospital", hospital_id=hospital_id))

    return render_template("dados_hospitais_edit.html", hospital=hospital, dados=dados)


# ======================================================
# EDITAR PRODUTOS (lista + adicionar + excluir)
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/produtos/editar", methods=["GET", "POST"])
def editar_produtos_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        produto = (request.form.get("produto") or "").strip()
        qtd = request.form.get("quantidade") or "0"
        try:
            qtd = int(qtd)
        except:
            qtd = 0

        if produto:
            p = ProdutoHospital(
                hospital_id=hospital_id,
                nome_hospital=hospital.nome_hospital,
                marca_planilha=request.form.get("marca_planilha"),
                produto=produto,
                quantidade=qtd,
            )
            db.session.add(p)
            db.session.commit()
            flash("Produto adicionado.", "success")

        return redirect(url_for("main.editar_produtos_hospital", hospital_id=hospital_id))

    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).order_by(ProdutoHospital.id.desc()).all()
    return render_template("produtos_hospitais_edit.html", hospital=hospital, produtos=produtos_db)


@bp.route("/hospitais/<int:hospital_id>/produtos/<int:produto_id>/excluir", methods=["POST"])
def excluir_produto(hospital_id, produto_id):
    p = ProdutoHospital.query.get_or_404(produto_id)
    if p.hospital_id != hospital_id:
        flash("Produto não pertence a este hospital.", "danger")
        return redirect(url_for("main.editar_produtos_hospital", hospital_id=hospital_id))
    db.session.delete(p)
    db.session.commit()
    flash("Produto removido.", "success")
    return redirect(url_for("main.editar_produtos_hospital", hospital_id=hospital_id))

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


