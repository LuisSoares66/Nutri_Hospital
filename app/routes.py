import io
import csv

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response
)

from app import db
from app.models import (
    Hospital, Contato, DadosHospital, ProdutoHospital
)

from app.excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
)

from app.pdf_report import build_hospital_report_pdf

bp = Blueprint("main", __name__)


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

    return render_template("hospital_form.html")


@bp.route("/hospitais/<int:hospital_id>/excluir", methods=["POST"])
def excluir_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    db.session.delete(hospital)
    db.session.commit()
    flash("Hospital excluído.", "success")
    return redirect(url_for("main.hospitais"))


# ======================================================
# CONTATOS
# ======================================================
@bp.route("/hospitais/<int:hospital_id>/contatos", methods=["GET", "POST"])
def contatos(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        c = Contato(
            hospital_id=hospital_id,
            hospital_nome=hospital.nome_hospital,
            nome_contato=request.form.get("nome_contato"),
            cargo=request.form.get("cargo"),
            telefone=request.form.get("telefone"),
        )
        db.session.add(c)
        db.session.commit()
        flash("Contato salvo.", "success")
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
        flash("Dados salvos.", "success")
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
@bp.route("/admin/importar_excel_uma_vez", methods=["POST"])
@admin_required
def importar_excel_uma_vez():
    # trava: se já existe hospital, não importa de novo
    if Hospital.query.first():
        flash("Importação já realizada.", "warning")
        return redirect(url_for("main.admin_panel"))

    data_dir = "data"

    # 1) HOSPITAIS
    for r in load_hospitais_from_excel(data_dir):
        h = Hospital(
            nome_hospital=r.get("nome_hospital"),
            endereco=r.get("endereco"),
            numero=r.get("numero"),
            complemento=r.get("complemento"),
            cep=r.get("cep"),
            cidade=r.get("cidade"),
            estado=r.get("estado"),
        )
        db.session.add(h)

    db.session.commit()

    flash("Importação inicial concluída.", "success")
    return redirect(url_for("main.hospitais"))


# ======================================================
# RESET TOTAL DO BANCO (ZERAR) - com senha
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
        flash("Senha ou confirmação inválida (senha incorreta).", "error")
        return redirect(url_for("main.admin_panel"))

    if confirm != "APAGAR":
        flash("Senha ou confirmação inválida (digite APAGAR).", "error")
        return redirect(url_for("main.admin_panel"))

    try:
        insp = inspect(db.engine)
        tables = insp.get_table_names()

        protected = {"alembic_version"}  # mantém controle do migrate

        with db.engine.begin() as conn:
            for t in tables:
                if t not in protected:
                    conn.execute(text(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE;'))

        db.session.commit()
        flash("Banco zerado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao zerar banco: {e}", "error")

    return redirect(url_for("main.admin_panel"))
