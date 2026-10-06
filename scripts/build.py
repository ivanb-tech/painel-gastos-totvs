#!/usr/bin/env python3
"""Gera o painel (dist/index.html) a partir das fichas de faturamento em data/*.xlsx.

Uso:
    python scripts/build.py                 # lê data/, escreve dist/index.html
    python scripts/build.py --data outra/pasta --out saida.html

Requisitos: Python 3.9+ e openpyxl (pip install -r requirements.txt).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("Falta a biblioteca openpyxl. Rode: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent

# Colunas da Ficha de Faturamento do Protheus usadas pelo painel.
# chave interna -> nome da coluna na planilha
COLUNAS = {
    "cliente": "NOME_CLIEN",
    "contrato": "CONTRATO",
    "prod": "PRODUTO",
    "desc": "DESCRICAO",
    "q": "QUANT",
    "vu": "VAL_UNIT",
    "vt": "VAL_TOTAL",
    "nf": "NF_ELETR",
    "em": "EMISSAO",
    "venc": "VENCTO",
    "bol": "VAL_BOLETO",
}
OBRIGATORIAS = {"DESCRICAO", "VAL_TOTAL", "EMISSAO"}


def numero(v) -> float:
    """Converte '16.032,20' ou 16032.2 em float."""
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def data_br(v) -> str:
    """Normaliza datas para dd/mm/aaaa (aceita texto ou célula de data do Excel)."""
    if v is None or v == "":
        return ""
    if isinstance(v, (dt.datetime, dt.date)):
        return v.strftime("%d/%m/%Y")
    s = str(v).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s[:10], fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    return s


def ler_planilha(caminho: Path) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True, read_only=True)
    linhas: list[dict] = []
    for ws in wb.worksheets:
        idx = None
        for row in ws.iter_rows(values_only=True):
            cel = [str(c).strip().upper() if c is not None else "" for c in row]
            if idx is None:
                # procura a linha de cabeçalho (a ficha do Protheus tem um título antes)
                if OBRIGATORIAS.issubset(cel):
                    idx = {nome: cel.index(nome) for nome in set(COLUNAS.values()) if nome in cel}
                continue
            def get(col):
                i = idx.get(col)
                return row[i] if i is not None and i < len(row) else None
            desc = get("DESCRICAO")
            emissao = data_br(get("EMISSAO"))
            if not desc or len(emissao) != 10:
                continue  # linha vazia, subtotal ou rodapé
            linhas.append({
                "cliente": str(get("NOME_CLIEN") or "").strip(),
                "contrato": str(get("CONTRATO") or "").strip(),
                "prod": str(get("PRODUTO") or "").strip(),
                "desc": str(desc).strip().upper(),
                "q": numero(get("QUANT")) or 1.0,
                "vu": numero(get("VAL_UNIT")) or numero(get("VAL_TOTAL")),
                "vt": numero(get("VAL_TOTAL")),
                "nf": str(get("NF_ELETR") or "").strip(),
                "em": emissao,
                "venc": data_br(get("VENCTO")),
                "bol": numero(get("VAL_BOLETO")),
            })
        if idx is not None:
            break  # usa a primeira aba que tem o cabeçalho
    if not linhas:
        print(f"  ! {caminho.name}: nenhuma linha reconhecida (cabeçalho com {sorted(OBRIGATORIAS)} não encontrado)")
    return linhas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=ROOT / "data", type=Path, help="pasta com as fichas .xlsx")
    ap.add_argument("--config", default=ROOT / "config" / "servicos.json", type=Path)
    ap.add_argument("--template", default=ROOT / "template" / "painel.html", type=Path)
    ap.add_argument("--out", default=ROOT / "dist" / "index.html", type=Path)
    args = ap.parse_args()

    arquivos = sorted(p for p in args.data.glob("*.xlsx") if not p.name.startswith("~$"))
    if not arquivos:
        print(f"Nenhuma planilha .xlsx encontrada em {args.data}")
        return 1

    todas: list[dict] = []
    for arq in arquivos:
        linhas = ler_planilha(arq)
        print(f"  - {arq.name}: {len(linhas)} itens")
        todas.extend(linhas)

    # Remove duplicados (a mesma NF/item aparecendo em mais de uma ficha exportada)
    vistos, dados = set(), []
    for r in todas:
        chave = (r["nf"], r["prod"], r["desc"], r["em"], round(r["vt"], 2))
        if chave in vistos:
            continue
        vistos.add(chave)
        dados.append(r)
    dup = len(todas) - len(dados)
    if not dados:
        print("Nenhum item de faturamento encontrado nas planilhas.")
        return 1

    config = json.loads(args.config.read_text(encoding="utf-8"))
    mapeados = {s.upper() for g in config["grupos"] for s in g.get("servicos", [])}
    novos = sorted({r["desc"] for r in dados} - mapeados)

    html = args.template.read_text(encoding="utf-8")
    html = (html
            .replace("__DATA__", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
            .replace("__CONFIG__", json.dumps(config, ensure_ascii=False, separators=(",", ":")))
            .replace("__BUILD__", dt.datetime.now().strftime("%d/%m/%Y %H:%M")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")

    total = sum(r["vt"] for r in dados)
    print(f"\nPainel gerado: {args.out}")
    print(f"  {len(dados)} itens · total R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if dup:
        print(f"  {dup} itens duplicados ignorados")
    if novos:
        print("\nAVISO: serviços sem grupo em config/servicos.json (aparecem como 'Outros'):")
        for d in novos:
            print(f"  - {d}")
        if "GITHUB_STEP_SUMMARY" in __import__("os").environ:
            with open(__import__("os").environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
                f.write("### Serviços sem grupo\nAdicione em `config/servicos.json`:\n\n")
                f.write("\n".join(f"- `{d}`" for d in novos) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
