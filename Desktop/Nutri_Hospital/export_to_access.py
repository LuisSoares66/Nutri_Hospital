import os
import sqlite3

# Requer Windows + "Microsoft Access Database Engine" instalado
import pyodbc

SQLITE_DB = "nutri_hospital.db"
ACCESS_FILE = "Nutri_Hospital.accdb"

def main():
    if not os.path.exists(SQLITE_DB):
        raise FileNotFoundError(f"Não achei {SQLITE_DB}. Rode o app e salve algum dado primeiro.")

    # Conecta no SQLite
    con_sqlite = sqlite3.connect(SQLITE_DB)
    con_sqlite.row_factory = sqlite3.Row
    cur = con_sqlite.cursor()

    rows = cur.execute("SELECT * FROM hospitais").fetchall()
    cols = [d[0] for d in cur.execute("PRAGMA table_info(hospitais)").fetchall()]  # simples

    # Cria o Access (o driver cria o arquivo se não existir)
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={os.path.abspath(ACCESS_FILE)};"
    )
    con_acc = pyodbc.connect(conn_str, autocommit=True)
    c = con_acc.cursor()

    # Recria tabela
    try:
        c.execute("DROP TABLE hospitais")
    except:
        pass

    # Tabela simples (campos texto como LONGTEXT)
    # Ajuste tipos se quiser mais controle.
    c.execute("""
        CREATE TABLE hospitais (
            id INTEGER,
            created_at TEXT,
            especialidade LONGTEXT,
            leitos INTEGER,
            leitos_uti INTEGER,
            fatores_decisorios LONGTEXT,
            prioridades_excelencia LONGTEXT,
            certificacoes LONGTEXT,
            tem_emtn TEXT,
            emtn_membros LONGTEXT,
            tem_comissao_feridas TEXT,
            comissao_feridas_membros LONGTEXT,
            nutricao_enteral_dia INTEGER,
            pacientes_tno_dia INTEGER,
            altas_orientadas_periodo LONGTEXT,
            quem_orienta_alta LONGTEXT,
            protocolo_evolucao_dieta LONGTEXT,
            protocolo_suplementacao_feridas LONGTEXT,
            maior_desafio LONGTEXT,
            dieta_padrao LONGTEXT,
            bomba_infusao LONGTEXT,
            tem_convenio TEXT,
            principais_convenios LONGTEXT,
            modelo_pagamento LONGTEXT,
            tem_reembolso TEXT,
            modelo_compras LONGTEXT,
            contrato_periodicidade LONGTEXT,
            nova_negociacao_quando LONGTEXT
        )
    """)

    # Insere
    insert_sql = """
        INSERT INTO hospitais (
            id, created_at, especialidade, leitos, leitos_uti, fatores_decisorios,
            prioridades_excelencia, certificacoes, tem_emtn, emtn_membros,
            tem_comissao_feridas, comissao_feridas_membros, nutricao_enteral_dia,
            pacientes_tno_dia, altas_orientadas_periodo, quem_orienta_alta,
            protocolo_evolucao_dieta, protocolo_suplementacao_feridas, maior_desafio,
            dieta_padrao, bomba_infusao, tem_convenio, principais_convenios,
            modelo_pagamento, tem_reembolso, modelo_compras, contrato_periodicidade,
            nova_negociacao_quando
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    for r in rows:
        c.execute(insert_sql, (
            r["id"], str(r["created_at"]), r["especialidade"], r["leitos"], r["leitos_uti"], r["fatores_decisorios"],
            r["prioridades_excelencia"], r["certificacoes"], r["tem_emtn"], r["emtn_membros"],
            r["tem_comissao_feridas"], r["comissao_feridas_membros"], r["nutricao_enteral_dia"],
            r["pacientes_tno_dia"], r["altas_orientadas_periodo"], r["quem_orienta_alta"],
            r["protocolo_evolucao_dieta"], r["protocolo_suplementacao_feridas"], r["maior_desafio"],
            r["dieta_padrao"], r["bomba_infusao"], r["tem_convenio"], r["principais_convenios"],
            r["modelo_pagamento"], r["tem_reembolso"], r["modelo_compras"], r["contrato_periodicidade"],
            r["nova_negociacao_quando"]
        ))

    con_acc.close()
    con_sqlite.close()
    print(f"OK! Arquivo gerado: {ACCESS_FILE}")

if __name__ == "__main__":
    main()
