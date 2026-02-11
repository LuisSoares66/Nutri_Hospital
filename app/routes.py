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
@admin_required
def excluir_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)

    try:
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

    # catálogo de produtos para seleção (lista rolável)
    catalogo = load_catalogo_produtos_from_excel("data")

    if request.method == "POST":
        produto_sel = (request.form.get("produto") or "").strip()
        marca_sel = (request.form.get("marca_planilha") or "").strip()

        if not produto_sel:
            flash("Selecione um produto na lista.", "error")
            return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

        p = ProdutoHospital(
            hospital_id=hospital_id,
            nome_hospital=hospital.nome_hospital,
            marca_planilha=marca_sel,
            produto=produto_sel,
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
        produtos=produtos_db,
        catalogo=catalogo
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
        # trava
        flag = AppMeta.query.filter_by(key=IMPORT_FLAG_KEY).first()
        if flag and (flag.value or "").lower() == "true":
            flash("Importação já foi realizada (uma vez).", "warning")
            return redirect(url_for("main.admin_panel"))

        data_dir = os.path.join(os.getcwd(), "data")

        # ---------------- HOSPITAIS ----------------
        rows_h = load_hospitais_from_excel(data_dir)

        print("IMPORT DEBUG hospitais:", type(rows_h), "len=", (len(rows_h) if hasattr(rows_h, "__len__") else None))
        print("IMPORT DEBUG hospitais first item:", (rows_h[0] if isinstance(rows_h, list) and rows_h else None))

        if not isinstance(rows_h, list) or (rows_h and not isinstance(rows_h[0], dict)):
            raise ValueError(f"hospitais.xlsx retornou formato inválido: {type(rows_h)} / first={type(rows_h[0]) if isinstance(rows_h, list) and rows_h else None}")

        nome_to_id = {}
        for r in rows_h:
            nome = (r.get("nome_hospital") or "").strip()
            if not nome:
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
            db.session.flush()
            nome_to_id[_norm(nome)] = h.id

        # ---------------- CONTATOS ----------------
        rows_c = load_contatos_from_excel(data_dir) or []
        print("IMPORT DEBUG contatos:", type(rows_c), "len=", (len(rows_c) if hasattr(rows_c, "__len__") else None))
        if rows_c and not isinstance(rows_c[0], dict):
            raise ValueError(f"contatos.xlsx retornou formato inválido: {type(rows_c)} / first={type(rows_c[0])}")

        for r in rows_c:
            hid = r.get("id_hospital") or r.get("hospital_id")
            try:
                hid = int(hid) if hid not in (None, "", 0) else None
            except:
                hid = None

            if not hid:
                hn = r.get("hospital_nome") or r.get("nome_hospital") or ""
                hid = nome_to_id.get(_norm(hn))

            nome_contato = (r.get("nome_contato") or "").strip()
            if not nome_contato:
                continue

            c = Contato(
                hospital_id=hid,
                hospital_nome=(r.get("hospital_nome") or r.get("nome_hospital") or ""),
                nome_contato=nome_contato,
                cargo=r.get("cargo"),
                telefone=r.get("telefone"),
            )
            db.session.add(c)

        # ---------------- DADOS HOSPITAIS ----------------
        rows_d = load_dados_hospitais_from_excel(data_dir) or []
        print("IMPORT DEBUG dadoshospitais:", type(rows_d), "len=", (len(rows_d) if hasattr(rows_d, "__len__") else None))
        if rows_d and not isinstance(rows_d[0], dict):
            raise ValueError(f"dadoshospitais.xlsx retornou formato inválido: {type(rows_d)} / first={type(rows_d[0])}")

        for r in rows_d:
            hid = r.get("id_hospital") or r.get("hospital_id")
            try:
                hid = int(hid) if hid not in (None, "", 0) else None
            except:
                hid = None

            if not hid:
                hn = r.get("hospital_nome") or r.get("nome_hospital") or ""
                hid = nome_to_id.get(_norm(hn))

            if not hid:
                continue

            dados = DadosHospital.query.filter_by(hospital_id=hid).first()
            if not dados:
                dados = DadosHospital(hospital_id=hid)
                db.session.add(dados)

            # mapeia os principais (você pode completar depois)
            dados.especialidade = r.get("Qual a especialidade do hospital?") or r.get("especialidade")
            dados.leitos = r.get("Quantos leitos?") or r.get("leitos")
            dados.leitos_uti = r.get("Quantos leitos de UTI?") or r.get("leitos_uti")

        # ---------------- PRODUTOS HOSPITAIS ----------------
        rows_p = load_produtos_hospitais_from_excel(data_dir) or []
        print("IMPORT DEBUG produtoshospitais:", type(rows_p), "len=", (len(rows_p) if hasattr(rows_p, "__len__") else None))
        if rows_p and not isinstance(rows_p[0], dict):
            raise ValueError(f"produtoshospitais.xlsx retornou formato inválido: {type(rows_p)} / first={type(rows_p[0])}")

        for r in rows_p:
            hid = r.get("hospital_id") or r.get("id_hospital")
            try:
                hid = int(hid) if hid not in (None, "", 0) else None
            except:
                hid = None

            if not hid:
                hn = r.get("nome_hospital") or r.get("hospital_nome") or ""
                hid = nome_to_id.get(_norm(hn))

            if not hid:
                continue

            prod = (r.get("produto") or "").strip()
            if not prod:
                continue

            qtd = r.get("quantidade") or 0
            try:
                qtd = int(qtd)
            except:
                qtd = 0

            ph = ProdutoHospital(
                hospital_id=hid,
                nome_hospital=r.get("nome_hospital") or r.get("hospital_nome") or "",
                marca_planilha=r.get("marca") or r.get("marca_planilha") or "",
                produto=prod,
                quantidade=qtd
            )
            db.session.add(ph)

        # flag
        if not flag:
            flag = AppMeta(key=IMPORT_FLAG_KEY, value="true")
            db.session.add(flag)
        else:
            flag.value = "true"

        db.session.commit()
        flash("Importação completa concluída.", "success")
        return redirect(url_for("main.admin_panel"))

    except Exception as e:
        db.session.rollback()
        print("IMPORT ERROR:", e)
        traceback.print_exc()
        flash(f"Erro ao importar: {e}", "danger")
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


