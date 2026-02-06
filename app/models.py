from . import db


class Hospital(db.Model):
    __tablename__ = "hospitais"

    id = db.Column(db.Integer, primary_key=True)  # id_hospital
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
        cascade="all, delete-orphan"
    )

    dados = db.relationship(
        "DadosHospital",
        backref="hospital",
        uselist=False,
        cascade="all, delete-orphan"
    )

    produtos = db.relationship(
        "ProdutoHospital",
        backref="hospital",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Hospital {self.id} - {self.nome_hospital}>"


class Contato(db.Model):
    __tablename__ = "contatos"

    id = db.Column(db.Integer, primary_key=True)  # id_contato

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitais.id"),
        nullable=True
    )

    hospital_nome = db.Column(db.String(255))
    nome_contato = db.Column(db.String(255), nullable=False)
    cargo = db.Column(db.String(255))
    telefone = db.Column(db.String(80))

    def __repr__(self):
        return f"<Contato {self.id} - {self.nome_contato}>"


class DadosHospital(db.Model):
    __tablename__ = "dados_hospitais"

    id = db.Column(db.Integer, primary_key=True)

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitais.id"),
        nullable=False,
        unique=True
    )

    especialidade = db.Column(db.Text)
    leitos = db.Column(db.String(50))
    leitos_uti = db.Column(db.String(50))

    fatores_decisorios = db.Column(db.Text)
    prioridades_atendimento = db.Column(db.Text)

    certificacao = db.Column(db.Text)

    emtn = db.Column(db.String(50))
    emtn_membros = db.Column(db.Text)

    comissao_feridas = db.Column(db.String(50))
    comissao_feridas_membros = db.Column(db.Text)

    nutricao_enteral_dia = db.Column(db.String(80))
    pacientes_tno_dia = db.Column(db.String(80))

    altas_orientadas = db.Column(db.String(120))
    quem_orienta_alta = db.Column(db.Text)

    protocolo_evolucao_dieta = db.Column(db.String(50))
    protocolo_evolucao_dieta_qual = db.Column(db.Text)

    protocolo_lesao_pressao = db.Column(db.String(50))
    protocolo_lesao_pressao_qual = db.Column(db.Text)

    maior_desafio = db.Column(db.Text)
    dieta_padrao = db.Column(db.Text)

    bomba_infusao_modelo = db.Column(db.Text)
    fornecedor = db.Column(db.Text)

    convenio_empresas = db.Column(db.Text)
    reembolso = db.Column(db.Text)

    modelo_compras = db.Column(db.Text)
    contrato_tipo = db.Column(db.Text)
    nova_etapa_negociacao = db.Column(db.Text)

    def __repr__(self):
        return f"<DadosHospital hospital_id={self.hospital_id}>"


class ProdutoHospital(db.Model):
    __tablename__ = "produtos_hospitais"

    id = db.Column(db.Integer, primary_key=True)

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitais.id"),
        nullable=False
    )

    nome_hospital = db.Column(db.String(255))
    marca_planilha = db.Column(db.String(50))  # PRODIET / NESTLÉ / DANONE / FRESENIUS

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

    def __repr__(self):
        return f"<ProdutoHospital {self.produto} ({self.quantidade})>"
    
from datetime import datetime
from app import db

class AppMeta(db.Model):
    __tablename__ = "app_meta"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

