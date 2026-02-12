import os
import re
import pandas as pd


def _path(data_dir: str, filename: str) -> str:
    return os.path.join(data_dir, filename)


def _norm_col(col: str) -> str:
    """
    Normaliza nome de coluna:
    - strip
    - lower
    - remove acentos simples
    - troca espaços e símbolos por underscore
    """
    if col is None:
        return ""
    c = str(col).strip().lower()

    # remove acentos comuns
    c = (
        c.replace("á", "a").replace("à", "a").replace("ã", "a").replace("â", "a")
         .replace("é", "e").replace("ê", "e")
         .replace("í", "i")
         .replace("ó", "o").replace("ô", "o").replace("õ", "o")
         .replace("ú", "u")
         .replace("ç", "c")
    )

    c = re.sub(r"[^a-z0-9]+", "_", c)  # tudo que não for letra/numero vira _
    c = re.sub(r"_+", "_", c).strip("_")
    return c


def _read_excel(fp: str, sheet_name=None) -> pd.DataFrame:
    df = pd.read_excel(fp, engine="openpyxl", sheet_name=sheet_name)
    # padroniza colunas
    df.columns = [_norm_col(c) for c in df.columns]
    # NaN -> ""
    df = df.fillna("")
    return df


def _to_int(val):
    try:
        if val == "" or val is None:
            return None
        return int(float(val))
    except Exception:
        return None


# ======================================================
# HOSPITAIS
# ======================================================
def load_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "hospitais.xlsx")
    if not os.path.exists(fp):
        return []

    df = _read_excel(fp)

    # aceitamos algumas variações comuns
    # ex: "id" pode vir como "idhospital", "id_hosp", etc
    aliases = {
        "id_hospital": ["id_hospital", "idhospital", "id", "hospital_id"],
        "nome_hospital": ["nome_hospital", "hospital", "nome", "nome_do_hospital"],
        "endereco": ["endereco", "endereco_hospital"],
        "numero": ["numero", "n", "num"],
        "complemento": ["complemento", "compl"],
        "cep": ["cep"],
        "cidade": ["cidade", "municipio"],
        "estado": ["estado", "uf"],
    }

    # cria colunas padrão se existirem alias
    for dest, possible in aliases.items():
        if dest in df.columns:
            continue
        for p in possible:
            if p in df.columns:
                df[dest] = df[p]
                break
        if dest not in df.columns:
            df[dest] = ""

    rows = []
    for _, r in df.iterrows():
        hid = _to_int(r.get("id_hospital"))
        nome = str(r.get("nome_hospital") or "").strip()
        if not hid or not nome:
            continue

        rows.append({
            "id_hospital": hid,
            "nome_hospital": nome,
            "endereco": str(r.get("endereco") or "").strip(),
            "numero": str(r.get("numero") or "").strip(),
            "complemento": str(r.get("complemento") or "").strip(),
            "cep": str(r.get("cep") or "").strip(),
            "cidade": str(r.get("cidade") or "").strip(),
            "estado": str(r.get("estado") or "").strip(),
        })

    return rows


# ======================================================
# CONTATOS
# ======================================================
def load_contatos_from_excel(data_dir: str):
    fp = _path(data_dir, "contatos.xlsx")
    if not os.path.exists(fp):
        return []

    df = _read_excel(fp)

    aliases = {
        "id_contato": ["id_contato", "idcontato", "id"],
        "id_hospital": ["id_hospital", "idhospital", "hospital_id"],
        "hospital_nome": ["hospital_nome", "nome_hospital", "hospital"],
        "nome_contato": ["nome_contato", "contato", "nome"],
        "cargo": ["cargo", "funcao"],
        "telefone": ["telefone", "fone", "celular"],
    }

    for dest, possible in aliases.items():
        if dest in df.columns:
            continue
        for p in possible:
            if p in df.columns:
                df[dest] = df[p]
                break
        if dest not in df.columns:
            df[dest] = ""

    rows = []
    for _, r in df.iterrows():
        nome_contato = str(r.get("nome_contato") or "").strip()
        if not nome_contato:
            continue

        rows.append({
            "id_contato": _to_int(r.get("id_contato")),
            "id_hospital": _to_int(r.get("id_hospital")),
            "hospital_nome": str(r.get("hospital_nome") or "").strip(),
            "nome_contato": nome_contato,
            "cargo": str(r.get("cargo") or "").strip(),
            "telefone": str(r.get("telefone") or "").strip(),
        })

    return rows


# ======================================================
# DADOS HOSPITAIS (mantém os nomes originais da planilha também)
# ======================================================
def load_dados_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "dadoshospitais.xlsx")
    if not os.path.exists(fp):
        return []

    df = _read_excel(fp)

    # precisamos garantir id_hospital
    if "id_hospital" not in df.columns:
        # tenta achar
        for c in ["idhospital", "hospital_id", "id"]:
            if c in df.columns:
                df["id_hospital"] = df[c]
                break
    if "id_hospital" not in df.columns:
        return []

    rows = []
    for _, r in df.iterrows():
        hid = _to_int(r.get("id_hospital"))
        if not hid:
            continue

        # devolve o dict inteiro (com colunas normalizadas)
        d = r.to_dict()
        d["id_hospital"] = hid
        rows.append(d)

    return rows


# ======================================================
# PRODUTOS HOSPITAIS
# ======================================================
def load_produtos_hospitais_from_excel(data_dir: str):
    fp = _path(data_dir, "produtoshospitais.xlsx")
    if not os.path.exists(fp):
        return []

    df = _read_excel(fp)

    aliases = {
        "hospital_id": ["hospital_id", "id_hospital", "idhospital"],
        "nome_hospital": ["nome_hospital", "hospital_nome", "hospital"],
        "produto": ["produto", "product"],
        "quantidade": ["quantidade", "qtd", "qtde"],
        "marca_planilha": ["marca_planilha", "marca", "planilha"],
    }

    for dest, possible in aliases.items():
        if dest in df.columns:
            continue
        for p in possible:
            if p in df.columns:
                df[dest] = df[p]
                break
        if dest not in df.columns:
            df[dest] = ""

    rows = []
    for _, r in df.iterrows():
        hid = _to_int(r.get("hospital_id"))
        produto = str(r.get("produto") or "").strip()
        if not hid or not produto:
            continue

        rows.append({
            "hospital_id": hid,
            "nome_hospital": str(r.get("nome_hospital") or "").strip(),
            "produto": produto,
            "quantidade": _to_int(r.get("quantidade")) or 0,
            "marca_planilha": str(r.get("marca_planilha") or "").strip(),
        })

    return rows
