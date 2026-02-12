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
import os
import pandas as pd

def load_catalogo_produtos_from_excel(data_dir: str = "data"):
    """
    Lê data/produtos.xlsx e retorna lista de dict:
      [{"marca_planilha": "...", "produto": "..."}, ...]

    Aceita variações de nome de coluna (Marca/Produto, marca_planilha/produto etc.).
    """
    path = os.path.join(data_dir, "produtos.xlsx")
    if not os.path.exists(path):
        return []

    df = pd.read_excel(path, dtype=str).fillna("")

    # tenta achar colunas
    cols = {c.strip().lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None

    col_marca = pick("marca", "marca_planilha", "marca planilha", "fabricante", "fornecedor", "brand")
    col_prod  = pick("produto", "descricao", "descrição", "nome_produto", "nome produto", "item", "product")

    # fallback: tenta achar pelo "contém"
    if not col_marca:
        for c in df.columns:
            lc = c.strip().lower()
            if "marca" in lc:
                col_marca = c
                break
    if not col_prod:
        for c in df.columns:
            lc = c.strip().lower()
            if "produto" in lc or "descr" in lc:
                col_prod = c
                break

    if not col_marca or not col_prod:
        # não achou as colunas necessárias
        return []

    out = []
    for _, row in df.iterrows():
        marca = (row.get(col_marca, "") or "").strip().upper()
        prod  = (row.get(col_prod, "") or "").strip()

        if not marca or not prod:
            continue

        out.append({"marca_planilha": marca, "produto": prod})

    return out


import os
import pandas as pd

def load_marcas_from_produtos_excel(data_dir: str = "data") -> list[str]:
    """
    Retorna as 'marcas' como os nomes das abas do data/produtos.xlsx
    """
    path = os.path.join(data_dir, "produtos.xlsx")
    if not os.path.exists(path):
        return []

    xls = pd.ExcelFile(path)
    # remove abas vazias/estranhas se quiser; aqui devolve todas
    marcas = [s.strip() for s in xls.sheet_names if str(s).strip()]
    return sorted(marcas)


def load_produtos_by_marca_from_produtos_excel(marca: str, data_dir: str = "data") -> list[str]:
    """
    Recebe a 'marca' (nome da aba) e retorna os produtos da coluna PRODUTO dessa aba.
    """
    path = os.path.join(data_dir, "produtos.xlsx")
    if not os.path.exists(path):
        return []

    marca = (marca or "").strip()
    if not marca:
        return []

    # lê somente a aba selecionada
    df = pd.read_excel(path, sheet_name=marca, dtype=str).fillna("")

    # coluna PRODUTO pode vir como "PRODUTO", "Produto", etc
    col_prod = None
    for c in df.columns:
        if str(c).strip().upper() == "PRODUTO":
            col_prod = c
            break
    if not col_prod:
        # fallback: primeira coluna
        col_prod = df.columns[0] if len(df.columns) else None

    if not col_prod:
        return []

    produtos = []
    for v in df[col_prod].tolist():
        p = (v or "").strip()
        if p:
            produtos.append(p)

    # remove duplicados mantendo ordem e ordena (se quiser manter ordem original, remova sorted)
    produtos = sorted(list(dict.fromkeys(produtos)))
    return produtos

