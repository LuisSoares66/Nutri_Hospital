"""add campos completos em dados_hospitais

Revision ID: 20260212_add_campos_dados_hospital
Revises: <COLOQUE_AQUI_SEU_DOWN_REVISION>
Create Date: 2026-02-12
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260212_add_campos_dados_hospital"
down_revision = "e797b7ad3ee2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS comissao_feridas TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS comissao_feridas_membros TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS nutricao_enteral_dia TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS pacientes_tno_dia TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS altas_orientadas TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS quem_orienta_alta TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS protocolo_evolucao_dieta TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS protocolo_evolucao_dieta_qual TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS protocolo_lesao_pressao TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS maior_desafio TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS dieta_padrao TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS bomba_infusao_modelo TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS fornecedor TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS convenio_empresas TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS convenio_empresas_modelo_pagamento TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS reembolso TEXT DEFAULT '';")

    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS modelo_compras TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS contrato_tipo TEXT DEFAULT '';")
    op.execute("ALTER TABLE dados_hospitais ADD COLUMN IF NOT EXISTS nova_etapa_negociacao TEXT DEFAULT '';")

def downgrade():
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS nova_etapa_negociacao;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS contrato_tipo;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS modelo_compras;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS reembolso;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS convenio_empresas_modelo_pagamento;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS convenio_empresas;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS fornecedor;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS bomba_infusao_modelo;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS dieta_padrao;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS maior_desafio;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS protocolo_lesao_pressao;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS protocolo_evolucao_dieta_qual;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS protocolo_evolucao_dieta;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS quem_orienta_alta;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS altas_orientadas;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS pacientes_tno_dia;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS nutricao_enteral_dia;")

    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS comissao_feridas_membros;")
    op.execute("ALTER TABLE dados_hospitais DROP COLUMN IF EXISTS comissao_feridas;")
