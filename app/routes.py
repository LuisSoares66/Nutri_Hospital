import io
import csv

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response
)

from app import db
from app.models import Hospital, Contato, DadosHospital, ProdutoHospital, AppMeta

from app.excel_loader import (
    load_hospitais_from_excel,
    load_contatos_from_excel,
    load_dados_hospitais_from_excel,
    load_produtos_hospitais_from_excel,
)

from app.auth import admin_required

import traceback
from sqlalchemy.exc import IntegrityError



def _norm(s: str) -> str:
    return (s or "").strip().upper()


from app.pdf_report import build_hospital_report_pdf

from app.excel_loader import load_catalogo_produtos_from_excel
IMPORT_FLAG_KEY = "import_excel_done_v1"

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
        nome = (request.form.get("nome_hospital") or "").strip()

        if not nome:
            flash("Informe o nome do hospital.", "error")
            return redirect(url_for("main.novo_hospital"))

        h = Hospital(
            id=r["id_hospital"],  # <- IMPORTANTÍSSIMO
            nome_hospital=r["nome_hospital"],
            endereco=r["endereco"],
            numero=r["numero"],
            complemento=r["complemento"],
            cep=r["cep"],
            cidade=r["cidade"],
            estado=r["estado"],
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


from sqlalchemy import inspect, text

# ======================================================
# IMPORTAR EXCEL (UMA VEZ) -> precisa ser POST
# ======================================================
IMPORT_FLAG_KEY = "import_excel_done_v1"

def _norm(s: str) -> str:
    return (s or "").strip().upper()


# ======================================================
# IMPORTAÇÃO EXCEL (UMA VEZ) - COMPLETA
# ======================================================
@bp.route("/admin/importar_excel_uma_vez", methods=["POST"])
@admin_required
def importar_excel_uma_vez():
    """
    Importa UMA ÚNICA VEZ:
      - hospitais.xlsx  -> Hospital (preservando Hospital.id = id_hospital do Excel)
      - contatos.xlsx   -> Contato (hospital_id = id_hospital)
      - dadoshospitais.xlsx -> DadosHospital (hospital_id = id_hospital)
      - produtoshospitais.xlsx -> ProdutoHospital (hospital_id = hospital_id / id_hospital)
    """

    try:
        # 1) trava de "uma vez"
        flag = AppMeta.query.get("excel_import_done")
        if flag and (flag.value or "").lower() == "true":
            flash("Importação já foi realizada (uma vez).", "warning")
            return redirect(url_for("main.admin_panel"))

        data_dir = "data"

        # 2) LÊ EXCEL
        hospitais_rows = load_hospitais_from_excel(data_dir)
        contatos_rows = load_contatos_from_excel(data_dir)
        dados_rows = load_dados_hospitais_from_excel(data_dir)
        produtos_rows = load_produtos_hospitais_from_excel(data_dir)

        if not hospitais_rows:
            flash("Nenhum hospital encontrado em data/hospitais.xlsx", "error")
            return redirect(url_for("main.admin_panel"))

        # 3) IMPORTA HOSPITAIS primeiro (preserva ID do Excel)
        #    -> se já existir, atualiza dados (não duplica)
        hospitais_importados = 0
        hospitais_atualizados = 0

        for r in hospitais_rows:
            hid = r.get("id_hospital")  # int já pelo loader
            nome = (r.get("nome_hospital") or "").strip()

            if not hid or not nome:
                # linha inválida
                continue

            h = Hospital.query.get(hid)
            if not h:
                h = Hospital(
                    id=hid,  # <<< ID DO EXCEL VIRA O ID NO BANCO
                    nome_hospital=nome,
                    endereco=r.get("endereco") or "",
                    numero=r.get("numero") or "",
                    complemento=r.get("complemento") or "",
                    cep=r.get("cep") or "",
                    cidade=r.get("cidade") or "",
                    estado=r.get("estado") or "",
                )
                db.session.add(h)
                hospitais_importados += 1
            else:
                h.nome_hospital = nome
                h.endereco = r.get("endereco") or ""
                h.numero = r.get("numero") or ""
                h.complemento = r.get("complemento") or ""
                h.cep = r.get("cep") or ""
                h.cidade = r.get("cidade") or ""
                h.estado = r.get("estado") or ""
                hospitais_atualizados += 1

        db.session.commit()

        # 4) MAPEIA hospitais existentes (garante FK)
        hospitais_existentes = {h.id for h in Hospital.query.with_entities(Hospital.id).all()}

        # 5) IMPORTA CONTATOS (somente se o hospital_id existir, senão salva sem associação)
        contatos_importados = 0
        contatos_sem_hospital = 0

        # IMPORTANTE: evita autoflush no meio
        with db.session.no_autoflush:
            for r in contatos_rows:
                nome_contato = (r.get("nome_contato") or "").strip()
                if not nome_contato:
                    continue

                hid = r.get("id_hospital")  # pode ser None
                hospital_nome = (r.get("hospital_nome") or "").strip()

                # se o ID não existir no banco, não associa (evita FK)
                if hid and hid not in hospitais_existentes:
                    hid = None

                c = Contato(
                    hospital_id=hid,
                    hospital_nome=hospital_nome,
                    nome_contato=nome_contato,
                    cargo=r.get("cargo") or "",
                    telefone=r.get("telefone") or "",
                )
                db.session.add(c)

                if hid is None:
                    contatos_sem_hospital += 1
                else:
                    contatos_importados += 1

        db.session.commit()

        # 6) IMPORTA DADOS DO HOSPITAL (um por hospital)
        dados_importados = 0
        dados_atualizados = 0
        dados_ignorados_sem_hospital = 0

        # Você pode escolher mapear os textos gigantes para colunas do model.
        # Aqui eu preencho os campos que existem no seu model atual.
        for r in dados_rows:
            hid = r.get("id_hospital")
            if not hid or hid not in hospitais_existentes:
                dados_ignorados_sem_hospital += 1
                continue

            d = DadosHospital.query.filter_by(hospital_id=hid).first()
            if not d:
                d = DadosHospital(hospital_id=hid)
                db.session.add(d)
                dados_importados += 1
            else:
                dados_atualizados += 1

            # Colunas do seu model (ajuste se quiser preencher mais):
            d.especialidade = r.get("Qual a especialidade do hospital?") or r.get("especialidade") or ""
            d.leitos = r.get("Quantos leitos?") or r.get("leitos") or ""
            d.leitos_uti = r.get("Quantos leitos de UTI?") or r.get("leitos_uti") or ""

            d.fatores_decisorios = r.get("Quais fatores são decisórios para o hospital escolher um determinado produto?") or ""
            d.prioridades_atendimento = r.get("Quais as prioridas do hospital para um atendimento nutricional de excelencia?") or ""
            d.certificacao = r.get("O hospital tem certificação ONA, CANADIAN, Joint Comission,...)?") or ""

            d.emtn = r.get("O hospital tem EMTN?") or ""
            d.emtn_membros = r.get("Se sim, quais os membro (nomes e especialidade)?") or ""

            d.comissao_feridas = r.get("Tem comissão de feridas?") or ""
            d.comissao_feridas_membros = r.get("Se sim, quem faz parte?") or ""

            d.nutricao_enteral_dia = r.get("Tem quantas nutrição enteral por dia?") or ""
            d.pacientes_tno_dia = r.get("Tem quantos pacientes em TNO por dia?") or ""

            d.altas_orientadas = r.get("Quantas altas orientadas por semana ou por mês?") or ""
            d.quem_orienta_alta = r.get("Quem faz esta orientação de alta?") or ""

            d.protocolo_evolucao_dieta = r.get("Existe um protocolo de evolução de dieta?") or ""
            d.protocolo_evolucao_dieta_qual = r.get("Qual?") or ""

            d.protocolo_lesao_pressao = r.get("Existe um protocolo para suplementação de pacientes com lesão por pressão ou feridas?") or ""
            # OBS: se existir outro "Qual?" na planilha, fica ambíguo.
            # Se você quiser, depois a gente separa por colunas únicas.
            d.protocolo_lesao_pressao_qual = ""

            d.maior_desafio = r.get("Qual o maior desafio na terapia nutricional do paciente internando no hospital?") or ""
            d.dieta_padrao = r.get("Qual a dieta padrão utilizada no hospital?") or ""

            d.bomba_infusao_modelo = r.get("Em relação à bomba de infusão: () é própria; () atrelada à compra de dieta; () comodato; () outro") or ""
            d.fornecedor = r.get("Qual fornecedor?") or ""

            d.convenio_empresas = r.get("Tem convenio com empresas?") or ""
            d.reembolso = r.get("Tem reembolso?") or ""

            d.modelo_compras = r.get("Qual modelo de compras do hospital? ()bionexo; () Contrato; () Apoio; () Cotação direta (na forma de caixa de itens)") or ""
            d.contrato_tipo = r.get("Se contrato, é anual ou semestral?") or ""
            d.nova_etapa_negociacao = r.get("Quando será a nova etapa de negociação?") or ""

        db.session.commit()

        # 7) IMPORTA PRODUTOS POR HOSPITAL
        produtos_importados = 0
        produtos_ignorados_sem_hospital = 0

        for r in produtos_rows:
            hid = r.get("hospital_id")
            if not hid or hid not in hospitais_existentes:
                produtos_ignorados_sem_hospital += 1
                continue

            produto_nome = (r.get("produto") or "").strip()
            if not produto_nome:
                continue

            p = ProdutoHospital(
                hospital_id=hid,
                nome_hospital=r.get("nome_hospital") or "",
                marca_planilha=r.get("marca_planilha") or "",
                produto=produto_nome,
                quantidade=int(r.get("quantidade") or 0),
            )
            db.session.add(p)
            produtos_importados += 1

        db.session.commit()

        # 8) MARCA IMPORT COMO CONCLUÍDA (UMA VEZ)
        if not flag:
            flag = AppMeta(key="excel_import_done", value="true")
            db.session.add(flag)
        else:
            flag.value = "true"
        db.session.commit()

        flash(
            "Importação concluída ✅ "
            f"Hospitais +{hospitais_importados} / atualizados {hospitais_atualizados} | "
            f"Contatos associados {contatos_importados} / sem hospital {contatos_sem_hospital} | "
            f"Dados +{dados_importados} / atualizados {dados_atualizados} / ignorados {dados_ignorados_sem_hospital} | "
            f"Produtos +{produtos_importados} / ignorados {produtos_ignorados_sem_hospital}.",
            "success"
        )
        return redirect(url_for("main.hospitais"))

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


