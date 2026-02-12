# app/excel_loader.py
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    # evita "nan"
    return "" if s.lower() == "nan" else s


def _to_int(v: Any, default: int = 0) -> int:
    s = _safe_str(v)
    if not s:
        return default
    try:
        return int(float(s))
    except Exception:
        return default


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _find_col(df: pd.DataFrame, exact_names_upper: List[str], contains_any: Optional[List[str]] = None) -> Optional[str]:
    """
    Encontra coluna por:
      1) match exato (case-insensitive)
      2) fallback por "contém" (case-insensitive)
    """
    if df is None or df.empty:
        return None

    cols = list(df.columns)
    upper_map = {str(c).strip().upper(): c for c in cols}

    for name in exact_names_upper:
        if name.upper() in upper_map:
            return upper_map[name.upper()]

    if contains_any:
        for c in cols:
            cu = str(c).strip().upper()
            for token in contains_any:
                if token.upper() in cu:
                    return c

    return None


# ======================================================
# HOSPITAIS (data/hospitais.xlsx)
# ======================================================
def load_hospitais_from_excel(data_dir: str = "data") -> List[Dict[str, Any]]:
    """
    Espera colunas típicas:
      id_hospital, nome_hospital, endereco, numero, complemento, cep, cidade, estado
    """
    path = os.path.join(data_dir, "hospitais.xlsx")
    if not os.path.exists(path):
        return []

    df = pd.read_excel(path, dtype=str).fillna("")
    df = _normalize_columns(df)

    # tenta localizar colunas
    col_id = _find_col(df, ["ID_HOSPITAL", "ID"], ["ID_HOSP"])
    col_nome = _find_col(df, ["NOME_HOSPITAL", "HOSPITAL", "NOME"], ["NOME"])
    col_end = _find_col(df, ["ENDERECO", "ENDEREÇO"], ["ENDERE"])
    col_num = _find_col(df, ["NUMERO", "NÚMERO"], ["NUM"])
    col_comp = _find_col(df, ["COMPLEMENTO"], ["COMPLE"])
    col_cep = _find_col(df, ["CEP"], ["CEP"])
    col_cid = _find_col(df, ["CIDADE"], ["CIDAD"])
    col_uf = _find_col(df, ["ESTADO", "UF"], ["UF", "ESTAD"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        hid = _to_int(r.get(col_id)) if col_id else 0
        nome = _safe_str(r.get(col_nome)) if col_nome else ""
        if not hid or not nome:
            continue

        out.append({
            "id_hospital": hid,
            "nome_hospital": nome,
            "endereco": _safe_str(r.get(col_end)) if col_end else "",
            "numero": _safe_str(r.get(col_num)) if col_num else "",
            "complemento": _safe_str(r.get(col_comp)) if col_comp else "",
            "cep": _safe_str(r.get(col_cep)) if col_cep else "",
            "cidade": _safe_str(r.get(col_cid)) if col_cid else "",
            "estado": _safe_str(r.get(col_uf)) if col_uf else "",
        })

    return out


# ======================================================
# CONTATOS (data/contatos.xlsx)
# ======================================================
def load_contatos_from_excel(data_dir: str = "data") -> List[Dict[str, Any]]:
    """
    Espera colunas típicas:
      id_hospital, hospital_nome, nome_contato, cargo, telefone
    """
    path = os.path.join(data_dir, "contatos.xlsx")
    if not os.path.exists(path):
        return []

    df = pd.read_excel(path, dtype=str).fillna("")
    df = _normalize_columns(df)

    col_id = _find_col(df, ["ID_HOSPITAL", "HOSPITAL_ID"], ["ID_HOSP"])
    col_hnome = _find_col(df, ["HOSPITAL_NOME", "NOME_HOSPITAL"], ["HOSPITAL"])
    col_nome = _find_col(df, ["NOME_CONTATO", "CONTATO"], ["CONTATO", "NOME"])
    col_cargo = _find_col(df, ["CARGO"], ["CARGO"])
    col_tel = _find_col(df, ["TELEFONE", "TEL"], ["TEL"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        nome = _safe_str(r.get(col_nome)) if col_nome else ""
        if not nome:
            continue

        out.append({
            "id_hospital": _to_int(r.get(col_id)) if col_id else None,
            "hospital_nome": _safe_str(r.get(col_hnome)) if col_hnome else "",
            "nome_contato": nome,
            "cargo": _safe_str(r.get(col_cargo)) if col_cargo else "",
            "telefone": _safe_str(r.get(col_tel)) if col_tel else "",
        })

    return out


# ======================================================
# DADOS DO HOSPITAL (data/dadoshospitais.xlsx)
# ======================================================
def load_dados_hospitais_from_excel(data_dir: str = "data") -> List[Dict[str, Any]]:
    """
    Lê o Excel e devolve uma lista de dicts por linha.
    Mantém as chaves exatamente como no cabeçalho, mas também inclui id_hospital como int.
    """
    path = os.path.join(data_dir, "dadoshospitais.xlsx")
    if not os.path.exists(path):
        return []

    df = pd.read_excel(path, dtype=str).fillna("")
    df = _normalize_columns(df)

    # garante id_hospital
    col_id = _find_col(df, ["ID_HOSPITAL"], ["ID_HOSP"])
    out: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        d = {str(k): _safe_str(v) for k, v in row.to_dict().items()}
        hid = _to_int(row.get(col_id)) if col_id else 0
        if not hid:
            continue
        d["id_hospital"] = hid
        out.append(d)

    return out


# ======================================================
# PRODUTOS POR HOSPITAL (data/produtoshospitais.xlsx)
# ======================================================
def load_produtos_hospitais_from_excel(data_dir: str = "data") -> List[Dict[str, Any]]:
    """
    Espera colunas típicas:
      hospital_id (ou id_hospital), nome_hospital, marca_planilha, produto, quantidade
    """
    path = os.path.join(data_dir, "produtoshospitais.xlsx")
    if not os.path.exists(path):
        return []

    df = pd.read_excel(path, dtype=str).fillna("")
    df = _normalize_columns(df)

    col_hid = _find_col(df, ["HOSPITAL_ID", "ID_HOSPITAL"], ["HOSPITAL", "ID_HOSP"])
    col_hnome = _find_col(df, ["NOME_HOSPITAL", "HOSPITAL_NOME"], ["HOSPITAL"])
    col_marca = _find_col(df, ["MARCA_PLANILHA", "MARCA"], ["MARCA"])
    col_prod = _find_col(df, ["PRODUTO"], ["PROD"])
    col_qtd = _find_col(df, ["QUANTIDADE", "QTD"], ["QTD", "QUANT"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        hid = _to_int(r.get(col_hid)) if col_hid else 0
        produto = _safe_str(r.get(col_prod)) if col_prod else ""
        if not hid or not produto:
            continue

        out.append({
            "hospital_id": hid,
            "nome_hospital": _safe_str(r.get(col_hnome)) if col_hnome else "",
            "marca_planilha": _safe_str(r.get(col_marca)) if col_marca else "",
            "produto": produto,
            "quantidade": _to_int(r.get(col_qtd), 0) if col_qtd else 0,
        })

    return out


# ======================================================
# CATÁLOGO DE PRODUTOS (data/produtos.xlsx) -> ABAS = MARCAS
# ======================================================
def load_marcas_from_produtos_excel(data_dir: str = "data") -> List[str]:
    """
    Retorna as marcas como os nomes das abas do data/produtos.xlsx
    """
    path = os.path.join(data_dir, "produtos.xlsx")
    if not os.path.exists(path):
        return []

    xls = pd.ExcelFile(path)
    marcas = [str(s).strip() for s in xls.sheet_names if str(s).strip()]
    return sorted(marcas)


def load_produtos_by_marca_from_produtos_excel(marca: str, data_dir: str = "data") -> List[str]:
    """
    Recebe a marca (nome da aba) e retorna os produtos dessa aba (coluna 'PRODUTO').
    """
    path = os.path.join(data_dir, "produtos.xlsx")
    if not os.path.exists(path):
        return []

    marca = _safe_str(marca)
    if not marca:
        return []

    df = pd.read_excel(path, sheet_name=marca, dtype=str).fillna("")
    df = _normalize_columns(df)

    # procura a coluna PRODUTO (case-insensitive)
    col_prod = None
    for c in df.columns:
        if str(c).strip().upper() == "PRODUTO":
            col_prod = c
            break

    # fallback: tenta por "contém"
    if not col_prod:
        col_prod = _find_col(df, ["PRODUTO"], ["PROD"])

    # fallback final: primeira coluna
    if not col_prod and len(df.columns) > 0:
        col_prod = df.columns[0]

    if not col_prod:
        return []

    produtos = []
    for v in df[col_prod].tolist():
        p = _safe_str(v)
        if p:
            produtos.append(p)

    # remove duplicados e ordena
    produtos = sorted(list(dict.fromkeys(produtos)))
    return produtos


# ======================================================
# (Opcional) Compat: se você tinha uma função antiga com esse nome,
# deixo aqui para não quebrar imports antigos.
# Ela retorna lista de dicts {"marca_planilha": <aba>, "produto": <produto>}
# ======================================================
def load_catalogo_produtos_from_excel(data_dir: str = "data") -> List[Dict[str, str]]:
    """
    Compat: monta um catálogo (marca_planilha, produto) lendo todas as abas.
    """
    marcas = load_marcas_from_produtos_excel(data_dir)
    out: List[Dict[str, str]] = []
    for m in marcas:
        prods = load_produtos_by_marca_from_produtos_excel(m, data_dir)
        for p in prods:
            out.append({"marca_planilha": m.strip(), "produto": p})
    return out
