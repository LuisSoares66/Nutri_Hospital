import os
import pandas as pd


def _path(data_dir: str, filename: str) -> str:
    return os.path.join(data_dir, filename)


def _read_excel(fp: str, sheet_name=None):
    if not os.path.exists(fp):
        return []
    df = pd.read_excel(fp, engine="openpyxl", sheet_name=sheet_name)
    # quando sheet_name=None, retorna dict de DataFrames (um por planilha)
    if isinstance(df, dict):
        for k in df:
            df[k] = df[k].fillna("")
        return {k: v.to_dict(orient="records") for k, v in df.items()}
    df = df.fillna("")
    return df.to_dict(orient="records")


def load_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "hospitais.xlsx")
    return _read_excel(fp)


def load_contatos_from_excel(data_dir: str):
    fp = _path(data_dir, "contatos.xlsx")
    return _read_excel(fp)


def load_dados_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "dadoshospitais.xlsx")
    return _read_excel(fp)


def load_produtos_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "produtoshospitais.xlsx")
    return _read_excel(fp)


def load_produtos_catalogo_from_excel(data_dir: str):
    """
    Lê produtos.xlsx que tem várias planilhas (PRODIET, NESTLÉ, DANONE, FRESENIUS)
    Retorna dict {nome_planilha: [rows]}
    """
    fp = _path(data_dir, "produtos.xlsx")
    return _read_excel(fp, sheet_name=None)
