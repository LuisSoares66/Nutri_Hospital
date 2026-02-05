from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return redirect(url_for("main.hospitais"))


@bp.route("/hospitais")
def hospitais():
    from app.models import Hospital
    hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
    return render_template("hospitais.html", hospitais=hospitais_db)


@bp.route("/hospitais/novo", methods=["GET", "POST"])
def novo_hospital():
    from app.models import Hospital

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
        flash("Hospital cadastrado com sucesso!", "success")
        return redirect(url_for("main.hospitais"))

    return render_template("hospital_form.html")


@bp.route("/contatos", methods=["GET", "POST"])
def contatos():
    from app.models import Contato, Hospital

    if request.method == "POST":
        contato = Contato(
            hospital_id=request.form.get("hospital_id") or None,
            hospital_nome=request.form.get("hospital_nome"),
            nome_contato=request.form.get("nome_contato"),
            cargo=request.form.get("cargo"),
            telefone=request.form.get("telefone"),
        )
        db.session.add(contato)
        db.session.commit()
        flash("Contato salvo com sucesso!", "success")
        return redirect(url_for("main.contatos"))

    contatos_db = Contato.query.order_by(Contato.nome_contato.asc()).all()
    hospitais_db = Hospital.query.order_by(Hospital.nome_hospital.asc()).all()
    return render_template("contatos.html", contatos=contatos_db, hospitais=hospitais_db)


@bp.route("/hospitais/<int:hospital_id>/dados", methods=["GET", "POST"])
def dados_hospital(hospital_id):
    from app.models import Hospital, DadosHospital

    hospital = Hospital.query.get_or_404(hospital_id)
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()

    if request.method == "POST":
        if not dados:
            dados = DadosHospital(hospital_id=hospital_id)
            db.session.add(dados)

        # Ajuste os nomes dos campos conforme seu HTML
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
        return redirect(url_for("main.hospitais"))

    return render_template("dados_hospital.html", hospital=hospital, dados=dados)


@bp.route("/hospitais/<int:hospital_id>/produtos", methods=["GET", "POST"])
def produtos_hospital(hospital_id):
    from app.models import Hospital, ProdutoHospital

    hospital = Hospital.query.get_or_404(hospital_id)

    if request.method == "POST":
        produto = ProdutoHospital(
            hospital_id=hospital_id,
            nome_hospital=hospital.nome_hospital,
            marca_planilha=request.form.get("marca_planilha"),
            produto=request.form.get("produto"),
            quantidade=int(request.form.get("quantidade") or 0),
        )
        db.session.add(produto)
        db.session.commit()
        flash("Produto adicionado!", "success")
        return redirect(url_for("main.produtos_hospital", hospital_id=hospital_id))

    produtos_db = ProdutoHospital.query.filter_by(hospital_id=hospital_id).order_by(ProdutoHospital.produto.asc()).all()
    return render_template("produtos_hospital.html", hospital=hospital, produtos=produtos_db)


@bp.route("/hospitais/<int:hospital_id>/relatorio")
def relatorio(hospital_id):
    from app.models import Hospital, Contato, DadosHospital, ProdutoHospital

    hospital = Hospital.query.get_or_404(hospital_id)
    contatos = Contato.query.filter_by(hospital_id=hospital_id).all()
    dados = DadosHospital.query.filter_by(hospital_id=hospital_id).first()
    produtos = ProdutoHospital.query.filter_by(hospital_id=hospital_id).all()

    return render_template("relatorio_view.html", hospital=hospital, contatos=contatos, dados=dados, produtos=produtos)
