import os
import pandas as pd


def _path(data_dir: str, filename: str) -> str:
    return os.path.join(data_dir, filename)


def _to_records(df: pd.DataFrame):
    df = df.copy()

    # normaliza nomes de colunas (remove espaços)
    df.columns = [str(c).strip() for c in df.columns]

    # troca NaN por ""
    df = df.fillna("")

    # retorna sempre lista de dict
    return df.to_dict(orient="records")


def load_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "hospitais.xlsx")
    if not os.path.exists(fp):
        return []

    df = pd.read_excel(fp, engine="openpyxl")

    # garante colunas esperadas (se faltarem, cria vazias)
    expected = ["id_hospital", "nome_hospital", "endereco", "numero", "complemento", "cep", "cidade", "estado"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    return _to_records(df)


def load_contatos_from_excel(data_dir: str):
    fp = _path(data_dir, "contatos.xlsx")
    if not os.path.exists(fp):
        return []

    df = pd.read_excel(fp, engine="openpyxl")
    expected = ["id_contato", "id_hospital", "hospital_nome", "nome_contato", "cargo", "telefone"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    return _to_records(df)


def load_dados_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "dadoshospitais.xlsx")
    if not os.path.exists(fp):
        return []

    df = pd.read_excel(fp, engine="openpyxl")

    # mantém as colunas exatamente como estão no Excel (perguntas longas)
    # só garante id_hospital
    if "id_hospital" not in df.columns:
        df["id_hospital"] = ""

    return _to_records(df)


def load_produtos_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "produtoshospitais.xlsx")
    if not os.path.exists(fp):
        return []

    df = pd.read_excel(fp, engine="openpyxl")

    # aceita hospital_id ou id_hospital
    if "hospital_id" not in df.columns and "id_hospital" not in df.columns:
        df["hospital_id"] = ""

    expected = ["hospital_id", "id_hospital", "nome_hospital", "produto", "quantidade", "marca_planilha"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    return _to_records(df)

def load_catalogo_produtos_from_excel(data_dir: str):
    """
    Lê data/produtos.xlsx (todas as planilhas) e retorna uma lista de itens:
    [{ "marca": "PRODIET", "produto": "Nome..." }, ...]
    """
    fp = os.path.join(data_dir, "produtos.xlsx")
    if not os.path.exists(fp):
        return []

    xls = pd.ExcelFile(fp, engine="openpyxl")
    itens = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        if df.empty:
            continue

        # tenta achar coluna "Produto" (case-insensitive)
        col_prod = None
        for c in df.columns:
            if str(c).strip().lower() == "produto":
                col_prod = c
                break
        if col_prod is None:
            continue

        for v in df[col_prod].fillna("").astype(str).tolist():
            nome = v.strip()
            if nome:
                itens.append({"marca": str(sheet).strip(), "produto": nome})

    # remove duplicados preservando ordem
    seen = set()
    out = []
    for it in itens:
        key = (it["marca"].upper(), it["produto"].upper())
        if key not in seen:
            seen.add(key)
            out.append(it)

    return out
