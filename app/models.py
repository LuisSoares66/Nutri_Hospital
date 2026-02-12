from datetime import datetime
from app.extensions import db



class AppMeta(db.Model):
    __tablename__ = "app_meta"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Hospital(db.Model):
    __tablename__ = "hospitais"

    id = db.Column(db.Integer, primary_key=True)
    nome_hospital = db.Column(db.String(255), nullable=False)

    endereco = db.Column(db.String(255))
    numero = db.Column(db.String(50))
    complemento = db.Column(db.String(120))
    cep = db.Column(db.String(20))
    cidade = db.Column(db.String(120))
    estado = db.Column(db.String(20))

    contatos = db.relationship(
        "Contato",
        backref="hospital",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    dados = db.relationship(
        "DadosHospital",
        backref="hospital",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    produtos = db.relationship(
        "ProdutoHospital",
        backref="hospital",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Contato(db.Model):
    __tablename__ = "contatos"

    id = db.Column(db.Integer, primary_key=True)

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitais.id", ondelete="SET NULL"),
        nullable=True
    )

    hospital_nome = db.Column(db.String(255))
    nome_contato = db.Column(db.String(255), nullable=False)
    cargo = db.Column(db.String(255))
    telefone = db.Column(db.String(80))


class DadosHospital(db.Model):
    __tablename__ = "dados_hospitais"

    id = db.Column(db.Integer, primary_key=True)

    # FK
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitais.id"), unique=True, nullable=False)

    # Colunas principais (já existiam no seu form inicial)
    especialidade = db.Column(db.Text, default="")
    leitos = db.Column(db.Text, default="")
    leitos_uti = db.Column(db.Text, default="")
    fatores_decisorios = db.Column(db.Text, default="")
    prioridades_atendimento = db.Column(db.Text, default="")
    certificacao = db.Column(db.Text, default="")
    emtn = db.Column(db.Text, default="")
    emtn_membros = db.Column(db.Text, default="")

    # Novas colunas (vindas do Excel dadoshospitais.xlsx)
    comissao_feridas = db.Column(db.Text, default="")
    comissao_feridas_membros = db.Column(db.Text, default="")

    nutricao_enteral_dia = db.Column(db.Text, default="")
    pacientes_tno_dia = db.Column(db.Text, default="")

    altas_orientadas = db.Column(db.Text, default="")
    quem_orienta_alta = db.Column(db.Text, default="")

    protocolo_evolucao_dieta = db.Column(db.Text, default="")
    protocolo_evolucao_dieta_qual = db.Column(db.Text, default="")

    protocolo_lesao_pressao = db.Column(db.Text, default="")

    maior_desafio = db.Column(db.Text, default="")
    dieta_padrao = db.Column(db.Text, default="")

    bomba_infusao_modelo = db.Column(db.Text, default="")
    fornecedor = db.Column(db.Text, default="")

    convenio_empresas = db.Column(db.Text, default="")
    convenio_empresas_modelo_pagamento = db.Column(db.Text, default="")

    reembolso = db.Column(db.Text, default="")

    modelo_compras = db.Column(db.Text, default="")
    contrato_tipo = db.Column(db.Text, default="")
    nova_etapa_negociacao = db.Column(db.Text, default="")



class ProdutoHospital(db.Model):
    __tablename__ = "produtos_hospitais"

    id = db.Column(db.Integer, primary_key=True)

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitais.id", ondelete="CASCADE"),
        nullable=False
    )

    nome_hospital = db.Column(db.String(255))
    marca_planilha = db.Column(db.String(50))

    produto = db.Column(db.String(255), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)

    embalagem = db.Column(db.String(120))
    referencia = db.Column(db.String(120))
    kcal = db.Column(db.String(50))
    ptn = db.Column(db.String(50))
    lip = db.Column(db.String(50))
    fibras = db.Column(db.String(50))
    sodio = db.Column(db.String(50))
    ferro = db.Column(db.String(50))
    potassio = db.Column(db.String(50))
    vit_b12 = db.Column(db.String(50))
    gordura_saturada = db.Column(db.String(50))
