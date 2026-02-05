import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def build_hospital_report_pdf(hospital, contatos, dados, produtos) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 2*cm

    def title(txt):
        nonlocal y
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, y, txt)
        y -= 0.8*cm

    def line(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(6*cm, y, (value or "")[:120])
        y -= 0.5*cm

    def paragraph(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, f"{label}:")
        y -= 0.45*cm
        c.setFont("Helvetica", 9)
        txt = (value or "").strip()
        if not txt:
            txt = "-"
        # quebra simples em linhas
        max_chars = 110
        for i in range(0, len(txt), max_chars):
            c.drawString(2*cm, y, txt[i:i+max_chars])
            y -= 0.45*cm
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm

        y -= 0.2*cm

    title("RELATÓRIO DO HOSPITAL")
    line("ID", str(hospital.id))
    line("Nome", hospital.nome_hospital)
    line("Endereço", f"{hospital.endereco or ''}, {hospital.numero or ''} {hospital.complemento or ''}".strip())
    line("CEP", hospital.cep)
    line("Cidade/Estado", f"{hospital.cidade or ''} - {hospital.estado or ''}".strip())

    y -= 0.3*cm
    title("CONTATOS")
    if contatos:
        for ct in contatos:
            line("Contato", f"{ct.nome_contato} | {ct.cargo or ''} | {ct.telefone or ''}")
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
    else:
        line("Contatos", "-")

    y -= 0.3*cm
    title("DADOS DO HOSPITAL")
    if dados:
        paragraph("Especialidade", dados.especialidade)
        paragraph("Leitos", dados.leitos)
        paragraph("Leitos UTI", dados.leitos_uti)
        paragraph("Fatores decisórios", dados.fatores_decisorios)
        paragraph("Prioridades (excelência)", dados.prioridades_atendimento)
        paragraph("Certificação", dados.certificacao)
        paragraph("EMTN", dados.emtn)
        paragraph("EMTN (membros)", dados.emtn_membros)
        paragraph("Comissão de feridas", dados.comissao_feridas)
        paragraph("Comissão de feridas (membros)", dados.comissao_feridas_membros)
        paragraph("Nutrição enteral/dia", dados.nutricao_enteral_dia)
        paragraph("Pacientes em TNO/dia", dados.pacientes_tno_dia)
        paragraph("Altas orientadas", dados.altas_orientadas)
        paragraph("Quem orienta alta", dados.quem_orienta_alta)
        paragraph("Protocolo evolução dieta", dados.protocolo_evolucao_dieta)
        paragraph("Qual (evolução dieta)", dados.protocolo_evolucao_dieta_qual)
        paragraph("Protocolo lesão/feridas", dados.protocolo_lesao_pressao)
        paragraph("Qual (lesão/feridas)", dados.protocolo_lesao_pressao_qual)
        paragraph("Maior desafio", dados.maior_desafio)
        paragraph("Dieta padrão", dados.dieta_padrao)
        paragraph("Bomba de infusão (modelo)", dados.bomba_infusao_modelo)
        paragraph("Fornecedor", dados.fornecedor)
        paragraph("Convênio / modelo pagamento", dados.convenio_empresas)
        paragraph("Reembolso", dados.reembolso)
        paragraph("Modelo de compras", dados.modelo_compras)
        paragraph("Contrato (anual/semestral)", dados.contrato_tipo)
        paragraph("Nova etapa de negociação", dados.nova_etapa_negociacao)
    else:
        line("Dados", "-")

    y -= 0.3*cm
    title("PRODUTOS DO HOSPITAL")
    if produtos:
        for p in produtos:
            line("Produto", f"{p.marca_planilha or ''} | {p.produto} | Qtd: {p.quantidade}")
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
    else:
        line("Produtos", "-")

    c.showPage()
    c.save()
    return buffer.getvalue()
