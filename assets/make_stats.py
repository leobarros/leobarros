#!/usr/bin/env python3
"""
Gera os cards de estatisticas do perfil (assets/stats.png e assets/langs.png).

Por que cards proprios em vez do github-readme-stats: aquele servico e uma
instancia publica compartilhada. Quando o GitHub busca a imagem pela primeira
vez, ele forca um calculo do zero; se aquele calculo pega rate limit, o card de
erro fica congelado no cache do camo e nao sai mais. Aqui os numeros viram PNG
commitado e servido pela raw.githubusercontent.com -- o camo nao intercepta
imagens de dominio do proprio GitHub, entao nao existe cache para envenenar.

Uso:
    python3 assets/make_stats.py                 # busca na API e gera os PNGs
    python3 assets/make_stats.py --from-json      # re-renderiza sem rede
    GITHUB_TOKEN=... python3 assets/make_stats.py # limites maiores de API

Dependencia: Pillow e numpy.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cardkit as ck  # noqa: E402

USER = "leobarros"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "assets", "stats-data.json")

STATS_W, STATS_H = 480, 200
LANGS_W, LANGS_H = 330, 200
SCALE = 2


# ------------------------------------------------------------------- coleta ---
def _get(path: str, token: str | None = None):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "profile-readme-stats")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def _search(kind: str, query: str, token: str | None = None) -> int:
    data = _get(f"/search/{kind}?q={query}&per_page=1", token)
    return int(data.get("total_count", 0))


def collect(token: str | None = None) -> dict:
    """Busca os numeros na API publica do GitHub."""
    user = _get(f"/users/{USER}", token)
    repos = _get(f"/users/{USER}/repos?per_page=100&type=owner", token)
    own = [r for r in repos if not r["fork"]]

    langs: dict[str, int] = {}
    for r in own:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1

    return {
        "gerado_em": dt.date.today().isoformat(),
        "usuario": USER,
        "estrelas_repos_proprios": sum(r["stargazers_count"] for r in own),
        "commits_publicos": _search("commits", f"author:{USER}", token),
        "pull_requests": _search("issues", f"author:{USER}+type:pr", token),
        "issues": _search("issues", f"author:{USER}+type:issue", token),
        "seguidores": user["followers"],
        "repos_publicos": user["public_repos"],
        "linguagens": dict(sorted(langs.items(), key=lambda kv: -kv[1])[:6]),
    }


# ------------------------------------------------------------------- desenho ---
def _header(d: ImageDraw.ImageDraw, w: int, title: str, note: str, s: int) -> int:
    """Titulo + nota a direita + linha separadora. Devolve o Y do conteudo."""
    px = lambda v: v * s  # noqa: E731
    d.text((px(20), px(17)), title, font=ck.font("semibold", px(16)), fill=ck.GLOW_B)
    if note:
        d.text(
            (px(w - 20), px(21)),
            note,
            font=ck.font("regular", px(10)),
            fill=ck.MUTED,
            anchor="ra",
        )
    d.line([(px(20), px(45)), (px(w - 20), px(45))], fill=ck.LINE, width=max(1, s))
    return px(58)


def render_stats(data: dict) -> Image.Image:
    s = SCALE
    px = lambda v: v * s  # noqa: E731
    img, d = ck.make_card(STATS_W, STATS_H, scale=s)
    top = _header(d, STATS_W, "Estatísticas", f"atualizado em {_br_date(data['gerado_em'])}", s)

    cells = [
        ("Estrelas · repos próprios", data["estrelas_repos_proprios"]),
        ("Commits públicos", data["commits_publicos"]),
        ("Pull requests", data["pull_requests"]),
        ("Issues", data["issues"]),
        ("Seguidores", data["seguidores"]),
        ("Repositórios públicos", data["repos_publicos"]),
    ]
    f_label = ck.font("regular", px(11))
    f_value = ck.font("bold", px(20))
    for i, (label, value) in enumerate(cells):
        x = px(20) + (i % 2) * px(226)
        y = top + (i // 2) * px(42)
        d.text((x, y), label, font=f_label, fill=ck.MUTED)
        d.text((x, y + px(15)), f"{value:,}".replace(",", "."), font=f_value, fill=ck.INK)

    return ck.finish_card(img, STATS_W, STATS_H, scale=s)


def render_langs(data: dict) -> Image.Image:
    s = SCALE
    px = lambda v: v * s  # noqa: E731
    img, d = ck.make_card(LANGS_W, LANGS_H, scale=s)
    top = _header(d, LANGS_W, "Linguagens", "por repositório", s) - px(2)

    langs = list(data["linguagens"].items())
    if not langs:
        return ck.finish_card(img, LANGS_W, LANGS_H, scale=s)

    maxv = max(v for _, v in langs)
    f_label = ck.font("medium", px(11))
    f_count = ck.font("regular", px(11))
    bar_x0, bar_x1 = px(18), px(268)
    track_w = bar_x1 - bar_x0
    for i, (name, count) in enumerate(langs):
        y = top + i * px(21)
        d.text((px(18), y), name, font=f_label, fill=ck.INK_DIM)

        bar_y = y + px(14)
        bar_h = px(7)
        d.rounded_rectangle(
            [bar_x0, bar_y, bar_x1, bar_y + bar_h], radius=bar_h // 2, fill=ck.LINE
        )
        w = int(track_w * (count / maxv))
        if w > bar_h:
            grad = ck.linear_gradient(w, bar_h, ck.GLOW_A, ck.GLOW_B)
            img.paste(grad, (bar_x0, bar_y), ck.rounded_mask((w, bar_h), bar_h // 2))
        d.text((px(LANGS_W - 18), y + px(1)), str(count), font=f_count, fill=ck.MUTED, anchor="ra")

    return ck.finish_card(img, LANGS_W, LANGS_H, scale=s)


def _br_date(iso: str) -> str:
    y, m, dd = iso.split("-")
    return f"{dd}/{m}/{y}"


# ---------------------------------------------------------------------- main ---
def main() -> None:
    ap = argparse.ArgumentParser(description="Gera os cards de estatisticas do perfil.")
    ap.add_argument("--from-json", action="store_true", help="nao busca na API, usa stats-data.json")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    data = None

    if not args.from_json:
        try:
            data = collect(token)
            with open(DATA_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            print(f"dados: buscados na API ({'com token' if token else 'sem token'})")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"aviso: falha ao consultar a API ({e}); tentando o JSON salvo", file=sys.stderr)

    if data is None:
        if not os.path.exists(DATA_FILE):
            raise SystemExit("Sem dados: nao consegui consultar a API nem achar assets/stats-data.json")
        with open(DATA_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"dados: reaproveitados de {os.path.relpath(DATA_FILE, ROOT)}")

    for name, img in (("stats", render_stats(data)), ("langs", render_langs(data))):
        out = os.path.join(ROOT, "assets", f"{name}.png")
        img.save(out, "PNG", optimize=True)
        print(f"ok: {os.path.relpath(out, ROOT)} ({img.width}x{img.height}, {os.path.getsize(out) / 1024:.0f} KB)")

    print(
        "numeros: "
        + ", ".join(
            f"{k}={v}" for k, v in data.items() if k not in ("linguagens", "gerado_em", "usuario")
        )
    )


if __name__ == "__main__":
    main()
