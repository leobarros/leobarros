#!/usr/bin/env python3
"""
Gera o banner do perfil (assets/banner.png).

Por que PNG e nao SVG: o GitHub nao renderiza SVG local referenciado por
caminho relativo em README de forma confiavel. PNG renderiza sempre.

Uso:
    python3 assets/make_banner.py            # gera assets/banner.png
    python3 assets/make_banner.py --scale 3  # mais nitido (arquivo maior)

Dependencia: Pillow (pip install Pillow) e numpy.
"""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cardkit as ck  # noqa: E402

# ---------------------------------------------------------------- conteudo ---
NOME = "Leonardo Barros"
HEADLINE = "SRE no Bradesco  ·  DevOps  ·  Cloud & Infraestrutura"
PROMPT = "~ $ whoami"
CHIPS = ["AWS", "Kubernetes", "Terraform", "Ansible", "Docker", "Observabilidade"]

TERMINAL = [
    (PROMPT, "prompt"),
    ("leonardo barros", "value"),
    ("", "muted"),
    ("~ $ cat foco.txt", "prompt"),
    ("confiabilidade · automação", "muted"),
    ("observabilidade", "muted"),
]

W, H = 1920, 480
PAD = 120


def build(scale: int) -> Image.Image:
    w, h = W * scale, H * scale
    s = scale

    def px(v: int) -> int:
        return v * s

    # -- fundo: gradiente + dois brilhos + grade discreta -------------------
    img = ck.linear_gradient(w, h, ck.BG_A, ck.BG_B)
    img = ck.add_glow(img, px(160), px(60), px(900), ck.GLOW_A, 0.30)
    img = ck.add_glow(img, px(1880), px(470), px(760), ck.GLOW_B, 0.20)

    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    step = px(48)
    for x in range(0, w, step):
        gd.line([(x, 0), (x, h)], fill=(255, 255, 255, 8), width=max(1, s // 2))
    for y in range(0, h, step):
        gd.line([(0, y), (w, y)], fill=(255, 255, 255, 8), width=max(1, s // 2))
    img = Image.alpha_composite(img.convert("RGBA"), grid)

    # -- faixa de acento na borda esquerda ----------------------------------
    strip = ck.linear_gradient(px(9), h, ck.GLOW_A, ck.GLOW_B).convert("RGBA")
    img.alpha_composite(strip, (0, 0))

    d = ImageDraw.Draw(img)

    # -- cartao de terminal (lado direito) ---------------------------------
    # o cartao e dimensionado pelo conteudo, entao nunca corta texto
    f_term = ck.font("mono", px(24))
    line_h, blank_h = px(34), px(20)
    text_h = sum(blank_h if not line else line_h for line, _ in TERMINAL)
    card_x0, card_x1, card_y0 = px(1290), px(1800), px(96)
    text_y0 = card_y0 + px(46) + px(24)
    card = (card_x0, card_y0, card_x1, text_y0 + text_h + px(20))

    d.rounded_rectangle(
        card, radius=px(18), fill=ck.SURFACE + (235,), outline=ck.LINE + (255,), width=max(1, s)
    )
    for cx, dot in zip(
        (card[0] + px(28), card[0] + px(50), card[0] + px(72)),
        ((34, 211, 238), (96, 165, 250), (71, 85, 105)),
    ):
        r = px(6)
        d.ellipse([cx - r, card[1] + px(24) - r, cx + r, card[1] + px(24) + r], fill=dot)
    d.line([(card[0], card[1] + px(46)), (card[2], card[1] + px(46))], fill=ck.LINE, width=max(1, s))

    colors = {"prompt": ck.GLOW_B, "value": ck.INK, "muted": ck.MUTED}
    ty = text_y0
    for line, kind in TERMINAL:
        if line:
            d.text((card[0] + px(30), ty), line, font=f_term, fill=colors[kind])
            ty += line_h
        else:
            ty += blank_h

    # -- bloco de texto principal ------------------------------------------
    x = px(PAD)
    d.text((x, px(72)), PROMPT, font=ck.font("mono_bold", px(30)), fill=ck.GLOW_B)
    d.text((x, px(116)), NOME, font=ck.font("bold", px(96)), fill=ck.INK)

    # barra de acento sob o nome
    bar = ck.linear_gradient(px(220), px(6), ck.GLOW_A, ck.GLOW_B).convert("RGBA")
    img.alpha_composite(bar, (x, px(248)))

    d.text((x, px(272)), HEADLINE, font=ck.font("medium", px(38)), fill=ck.INK_DIM)

    # -- chips de tecnologia ------------------------------------------------
    f_chip = ck.font("medium", px(27))
    chip_h, gap, padx = px(52), px(14), px(22)
    y0, y1 = px(362), px(362) + chip_h
    cx = x
    max_x = px(W - PAD)
    for label in CHIPS:
        cw = ck.text_width(d, label, f_chip) + padx * 2
        if cx + cw > max_x:  # nunca estoura a margem
            break
        d.rounded_rectangle(
            [cx, y0, cx + cw, y1],
            radius=chip_h // 2,
            fill=(15, 23, 42, 200),
            outline=ck.LINE + (255,),
            width=max(1, s),
        )
        tw = ck.text_width(d, label, f_chip)
        d.text(
            (cx + (cw - tw) // 2, y0 + chip_h // 2),
            label,
            font=f_chip,
            fill=(203, 213, 225),
            anchor="lm",
        )
        cx += cw + gap

    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera o banner do perfil.")
    ap.add_argument("--scale", type=int, default=2, help="fator de supersampling (padrao 2)")
    ap.add_argument("--out", default="assets/banner.png", help="caminho de saida")
    args = ap.parse_args()

    img = build(max(1, args.scale))
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"ok: {out} ({img.width}x{img.height}, {os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
