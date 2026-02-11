from datetime import datetime
from app import db


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

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitais.id", ondelete="CASCADE"),
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
