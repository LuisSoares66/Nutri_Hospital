import os
from typing import List, Dict, Any, Optional

import pandas as pd


def _safe_path(data_dir: str, filename: str) -> str:
    return os.path.join(data_dir, filename)


def _read_xlsx(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    # lê tudo como string pra evitar "342.0" e bagunça
    df = pd.read_excel(path, dtype=str)
    # remove colunas "Unnamed: x"
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    # strip nos nomes de colunas
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _strip(v: Any) -> str:
    return ("" if v is None else str(v)).strip()


def _to_int(v: Any) -> Optional[int]:
    """
    Converte '342', '342.0', 342.0, ' 342 ' -> 342
    Retorna None se vazio/inválido.
    """
    s = _strip(v)
    if not s:
        return None
    try:
        # trata '342.0000'
        return int(float(s.replace(",", ".")))
    except Exception:
        return None


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Encontra coluna pelo nome exato ou por comparação case-insensitive.
    """
    cols = list(df.columns)
    cols_upper = {c.upper(): c for c in cols}

    for cand in candidates:
        c = cand.strip()
        if c in cols:
            return c
        cu = c.upper()
        if cu in cols_upper:
            return cols_upper[cu]

    return None


def _get(df_row: pd.Series, col: Optional[str], default: Any = "") -> Any:
    if not col:
        return default
    return df_row.get(col, default)


# ======================================================
# HOSPITAIS
# ======================================================
def load_hospitais_from_excel(data_dir: str) -> List[Dict[str, Any]]:
    """
    Espera data/hospitais.xlsx.
    Retorna lista de dict:
      {
        "id_hospital": int,
        "nome_hospital": str,
        "endereco": str,
        "numero": str,
        "complemento": str,
        "cep": str,
        "cidade": str,
        "estado": str,
      }
    """
    path = _safe_path(data_dir, "hospitais.xlsx")
    df = _read_xlsx(path)
    if df.empty:
        return []

    c_id = _find_col(df, ["id_hospital", "id", "codigo", "cod_hospital"])
    c_nome = _find_col(df, ["nome_hospital", "hospital", "nome", "razao_social"])
    c_end = _find_col(df, ["endereco", "endereço", "logradouro"])
    c_num = _find_col(df, ["numero", "número", "num"])
    c_comp = _find_col(df, ["complemento", "compl"])
    c_cep = _find_col(df, ["cep"])
    c_cid = _find_col(df, ["cidade", "município", "municipio"])
    c_uf = _find_col(df, ["estado", "uf"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        hid = _to_int(_get(r, c_id))
        nome = _strip(_get(r, c_nome))

        # ignora linhas vazias
        if not hid and not nome:
            continue

        out.append(
            {
                "id_hospital": hid,
                "nome_hospital": nome,
                "endereco": _strip(_get(r, c_end)),
                "numero": _strip(_get(r, c_num)),
                "complemento": _strip(_get(r, c_comp)),
                "cep": _strip(_get(r, c_cep)),
                "cidade": _strip(_get(r, c_cid)),
                "estado": _strip(_get(r, c_uf)),
            }
        )
    return out


# ======================================================
# CONTATOS
# ======================================================
def load_contatos_from_excel(data_dir: str) -> List[Dict[str, Any]]:
    """
    Espera data/contatos.xlsx.
    Retorna:
      {
        "id_hospital": int,
        "hospital_nome": str,
        "nome_contato": str,
        "cargo": str,
        "telefone": str
      }
    """
    path = _safe_path(data_dir, "contatos.xlsx")
    df = _read_xlsx(path)
    if df.empty:
        return []

    c_hid = _find_col(df, ["id_hospital", "hospital_id", "id", "cod_hospital"])
    c_hnome = _find_col(df, ["hospital_nome", "nome_hospital", "hospital", "nome"])
    c_nome = _find_col(df, ["nome_contato", "contato", "nome", "responsavel", "responsável"])
    c_cargo = _find_col(df, ["cargo", "funcao", "função"])
    c_tel = _find_col(df, ["telefone", "fone", "celular", "whatsapp"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        nome_contato = _strip(_get(r, c_nome))
        if not nome_contato:
            continue

        out.append(
            {
                "id_hospital": _to_int(_get(r, c_hid)),
                "hospital_nome": _strip(_get(r, c_hnome)),
                "nome_contato": nome_contato,
                "cargo": _strip(_get(r, c_cargo)),
                "telefone": _strip(_get(r, c_tel)),
            }
        )

    return out


# ======================================================
# DADOS HOSPITAIS
# ======================================================
def load_dados_hospitais_from_excel(data_dir: str) -> List[Dict[str, Any]]:
    """
    Espera data/dadoshospitais.xlsx.
    Retorna list[dict] com:
      - id_hospital
      - e o resto das colunas como texto (mantém perguntas longas)
    """
    path = _safe_path(data_dir, "dadoshospitais.xlsx")
    df = _read_xlsx(path)
    if df.empty:
        return []

    # tenta achar a coluna de id
    c_id = _find_col(df, ["id_hospital", "hospital_id", "id", "cod_hospital"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        row_dict = {str(k).strip(): _strip(v) for k, v in r.to_dict().items()}
        hid = _to_int(row_dict.get(c_id) if c_id else row_dict.get("id_hospital"))
        row_dict["id_hospital"] = hid

        # ignora linha vazia
        if not hid and not any(v for k, v in row_dict.items() if k != "id_hospital"):
            continue

        out.append(row_dict)

    return out


# ======================================================
# PRODUTOS POR HOSPITAL
# ======================================================
def load_produtos_hospitais_from_excel(data_dir: str) -> List[Dict[str, Any]]:
    """
    Espera data/produtoshospitais.xlsx.
    Retorna:
      {
        "hospital_id": int,
        "id_hospital": int (fallback),
        "nome_hospital": str,
        "marca_planilha": str,
        "produto": str,
        "quantidade": int
      }
    """
    path = _safe_path(data_dir, "produtoshospitais.xlsx")
    df = _read_xlsx(path)
    if df.empty:
        return []

    c_hid = _find_col(df, ["hospital_id", "id_hospital", "id", "cod_hospital"])
    c_nome_h = _find_col(df, ["nome_hospital", "hospital_nome", "hospital"])
    c_marca = _find_col(df, ["marca_planilha", "marca", "fornecedor", "fabricante"])
    c_prod = _find_col(df, ["produto", "descricao", "descrição", "item"])
    c_qtd = _find_col(df, ["quantidade", "qtd", "qtde"])

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        produto = _strip(_get(r, c_prod))
        if not produto:
            continue

        hid = _to_int(_get(r, c_hid))
        qtd = _to_int(_get(r, c_qtd)) or 0

        out.append(
            {
                "hospital_id": hid,
                "id_hospital": hid,  # compatibilidade (se seu route buscar id_hospital)
                "nome_hospital": _strip(_get(r, c_nome_h)),
                "marca_planilha": _strip(_get(r, c_marca)),
                "produto": produto,
                "quantidade": qtd,
            }
        )

    return out


# ======================================================
# CATÁLOGO DE PRODUTOS (OPCIONAL)
# ======================================================
def load_catalogo_produtos_from_excel(data_dir: str) -> List[Dict[str, Any]]:
    """
    Opcional (se você tiver um catálogo separado em data/catalogo_produtos.xlsx).
    Retorna lista de dict com colunas livres (mantém o que tiver).
    """
    path = _safe_path(data_dir, "catalogo_produtos.xlsx")
    df = _read_xlsx(path)
    if df.empty:
        return []

    out: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        d = {str(k).strip(): _strip(v) for k, v in r.to_dict().items()}
        # ignora linha vazia
        if not any(d.values()):
            continue
        out.append(d)
    return out
