import os
from datetime import datetime

from sqlalchemy import create_engine, text

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

def get_db_url():
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url or "sqlite:///nutri_hospital.db"

CAMPOS = [
    ("id", "ID"),
    ("created_at", "Criado em"),
    ("especialidade", "Especialidade"),
    ("leitos", "Leitos"),
    ("leitos_uti", "UTI"),
    ("fatores_decisorios", "Fatores decisórios"),
    ("prioridades_excelencia", "Prioridades"),
    ("certificacoes", "Certificações"),
    ("tem_emtn", "EMTN"),
    ("emtn_membros", "Membros EMTN"),
    ("tem_comissao_feridas", "Comissão feridas"),
    ("comissao_feridas_membros", "Membros feridas"),
    ("nutricao_enteral_dia", "Enteral/dia"),
    ("pacientes_tno_dia", "TNO/dia"),
    ("altas_orientadas_periodo", "Altas orientadas"),
    ("quem_orienta_alta", "Quem orienta alta"),
    ("protocolo_evolucao_dieta", "Protocolo dieta"),
    ("protocolo_suplementacao_feridas", "Protocolo feridas"),
    ("maior_desafio", "Maior desafio"),
    ("dieta_padrao", "Dieta padrão"),
    ("bomba_infusao", "Bomba infusão"),
    ("tem_convenio", "Convênio"),
    ("principais_convenios", "Principais convênios"),
    ("modelo_pagamento", "Modelo pagamento"),
    ("tem_reembolso", "Reembolso"),
    ("modelo_compras", "Modelo compras"),
    ("contrato_periodicidade", "Contrato"),
    ("nova_negociacao_quando", "Nova negociação"),
]

def wrap_text(c, text_value, max_chars):
    if text_value is None:
        return [""]
    s = str(text_value).replace("\n", " ").strip()
    if not s:
        return [""]
    lines = []
    while len(s) > max_chars:
        cut = s.rfind(" ", 0, max_chars)
        if cut == -1:
            cut = max_chars
        lines.append(s[:cut].strip())
        s = s[cut:].strip()
    lines.append(s)
    return lines

def gerar_pdf(saida="relatorio_hospitais.pdf"):
    db_url = get_db_url()
    engine = create_engine(db_url)

    # Busca dados
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM hospitais ORDER BY created_at DESC")).mappings().all()

    # PDF em paisagem pra caber mais colunas
    page_size = landscape(A4)
    c = canvas.Canvas(saida, pagesize=page_size)
    width, height = page_size

    margem = 12 * mm
    y = height - margem

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margem, y, "Nutri_Hospital - Relatório Completo (Hospitais)")
    y -= 10 * mm

    c.setFont("Helvetica", 9)
    c.drawString(margem, y, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 8 * mm

    if not rows:
        c.setFont("Helvetica", 11)
        c.drawString(margem, y, "Nenhum registro encontrado.")
        c.save()
        return saida

    # Layout: lista por registro (mais legível que tabela gigante no PDF)
    c.setFont("Helvetica", 10)
    for r in rows:
        # quebra de página se necessário
        if y < 25 * mm:
            c.showPage()
            y = height - margem
            c.setFont("Helvetica", 10)

        c.setFont("Helvetica-Bold", 11)
        c.drawString(margem, y, f"Registro ID {r.get('id')} — {r.get('created_at')}")
        y -= 6 * mm

        c.setFont("Helvetica", 10)
        for key, label in CAMPOS:
            if key in ("id", "created_at"):
                continue
            val = r.get(key, "")
            lines = wrap_text(c, val, max_chars=140)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margem, y, f"{label}:")
            c.setFont("Helvetica", 10)

            # primeira linha ao lado do label
            first = lines[0] if lines else ""
            c.drawString(margem + 45*mm, y, first)
            y -= 5 * mm

            # linhas adicionais
            for extra in lines[1:]:
                if y < 25 * mm:
                    c.showPage()
                    y = height - margem
                    c.setFont("Helvetica", 10)
                c.drawString(margem + 45*mm, y, extra)
                y -= 5 * mm

            if y < 25 * mm:
                c.showPage()
                y = height - margem
                c.setFont("Helvetica", 10)

        y -= 4 * mm
        c.line(margem, y, width - margem, y)
        y -= 6 * mm

    c.save()
    return saida

if __name__ == "__main__":
    path = gerar_pdf()
    print(f"PDF gerado: {path}")
