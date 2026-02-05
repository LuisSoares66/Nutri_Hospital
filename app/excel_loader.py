import os
import pandas as pd

def _path(data_dir: str, filename: str) -> str:
    return os.path.join(data_dir, filename)

def load_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "hospitais.xlsx")
    if not os.path.exists(fp):
        return []
    df = pd.read_excel(fp, engine="openpyxl")
    df = df.fillna("")
    # colunas esperadas:
    # id_hospital, nome_hospital, endereco, numero, complemento, cep, cidade, estado
    return df.to_dict(orient="records")

def load_contatos_from_excel(data_dir: str):
    fp = _path(data_dir, "contatos.xlsx")
    if not os.path.exists(fp):
        return []
    df = pd.read_excel(fp, engine="openpyxl")
    df = df.fillna("")
    return df.to_dict(orient="records")

def load_dados_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "dadoshospitais.xlsx")
    if not os.path.exists(fp):
        return []
    df = pd.read_excel(fp, engine="openpyxl")
    df = df.fillna("")
    return df.to_dict(orient="records")

def load_produtos_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "produtoshospitais.xlsx")
    if not os.path.exists(fp):
        return []
    df = pd.read_excel(fp, engine="openpyxl")
    df = df.fillna("")
    return df.to_dict(orient="records")

def load_catalogo_produtos(data_dir: str):
    """
    Lê produtos.xlsx com as planilhas:
    PRODIET, NESTLÉ, DANONE, FRESENIUS
    Retorna dict: { "PRODIET": [ {Produto, Embalagem,...}, ... ], ... }
    """
    fp = _path(data_dir, "produtos.xlsx")
    if not os.path.exists(fp):
        return {}

    xls = pd.ExcelFile(fp, engine="openpyxl")
    catalogo = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(fp, sheet_name=sheet, engine="openpyxl").fillna("")
        catalogo[sheet] = df.to_dict(orient="records")
    return catalogo
