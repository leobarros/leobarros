#!/usr/bin/env python3
"""
Gera o banner do perfil (assets/banner.png).

Por que PNG e nao SVG: o GitHub nao renderiza SVG local referenciado por
caminho relativo em README de forma confiavel. PNG renderiza sempre.

Uso:
    python3 assets/make_banner.py            # gera assets/banner.png
    python3 assets/make_banner.py --scale 3  # mais nitido (arquivo maior)

Dependencia: Pillow (pip install Pillow).
"""

from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

# ------------------------------------------------------------------ paleta ---
BG_A = (9, 14, 26)        # fundo, canto superior esquerdo
BG_B = (17, 24, 42)       # fundo, canto inferior direito
GLOW_A = (37, 99, 235)    # azul
GLOW_B = (34, 211, 238)   # ciano
INK = (248, 250, 252)     # texto principal
INK_DIM = (148, 163, 184)  # texto secundario
LINE = (30, 41, 59)       # bordas
SURFACE = (13, 19, 33)    # superficie dos cartoes
MUTED = (125, 140, 163)

W, H = 1920, 480
PAD = 120

FONT_CANDIDATES = {
    "bold": [
        "~/.local/share/fonts/FiraSans-Bold.ttf",
        "/usr/share/fonts/truetype/fira/FiraSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "medium": [
        "~/.local/share/fonts/FiraSans-Medium.ttf",
        "/usr/share/fonts/truetype/fira/FiraSans-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "regular": [
        "~/.local/share/fonts/FiraSans-Regular.ttf",
        "/usr/share/fonts/truetype/fira/FiraSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "~/.local/share/fonts/FiraCode-Regular.ttf",
    ],
    "mono_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "~/.local/share/fonts/FiraCode-Bold.ttf",
    ],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    """Carrega a primeira fonte disponivel da lista, com fallback claro."""
    for path in FONT_CANDIDATES[kind]:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(
        f"Nenhuma fonte encontrada para '{kind}'. Edite FONT_CANDIDATES no script."
    )


def linear_gradient(w: int, h: int, c0, c1) -> Image.Image:
    """Gradiente diagonal suave entre duas cores."""
    t = (np.add.outer(np.linspace(0, 1, h), np.linspace(0, 1, w)) / 2.0)[..., None]
    c0a, c1a = np.array(c0, float), np.array(c1, float)
    rgb = (c0a + (c1a - c0a) * t).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")


def radial_glow(w: int, h: int, color, cx: float, cy: float, radius: float) -> Image.Image:
    """Mascara de brilho radial (0-255) usada para colorir o fundo."""
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xs - cx) / radius) ** 2 + ((ys - cy) / radius) ** 2)
    a = np.clip(1.0 - d, 0.0, 1.0) ** 1.8
    return Image.fromarray((a * 255).astype(np.uint8), "L")


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return m


def text_width(draw: ImageDraw.ImageDraw, s: str, f: ImageFont.FreeTypeFont) -> int:
    return int(draw.textlength(s, font=f))


def build(scale: int) -> Image.Image:
    w, h = W * scale, H * scale
    s = scale

    def px(v: int) -> int:
        return v * s

    # -- fundo: gradiente + dois brilhos + grade discreta -------------------
    img = linear_gradient(w, h, BG_A, BG_B)

    for color, cx, cy, radius, alpha in (
        (GLOW_A, px(160), px(60), px(900), 0.30),
        (GLOW_B, px(1880), px(470), px(760), 0.20),
    ):
        glow = Image.new("RGB", (w, h), color)
        mask = radial_glow(w, h, color, cx, cy, radius).point(lambda v: int(v * alpha))
        img = Image.composite(glow, img, mask)

    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    step = px(48)
    for x in range(0, w, step):
        gd.line([(x, 0), (x, h)], fill=(255, 255, 255, 8), width=max(1, s // 2))
    for y in range(0, h, step):
        gd.line([(0, y), (w, y)], fill=(255, 255, 255, 8), width=max(1, s // 2))
    img = Image.alpha_composite(img.convert("RGBA"), grid)

    # -- faixa de acento na borda esquerda ----------------------------------
    strip = linear_gradient(px(9), h, GLOW_A, GLOW_B).convert("RGBA")
    img.alpha_composite(strip, (0, 0))

    d = ImageDraw.Draw(img)

    # -- cartao de terminal (lado direito) ---------------------------------
    # o cartao e dimensionado pelo conteudo, entao nunca corta texto
    f_term = font("mono", px(24))
    line_h, blank_h = px(34), px(20)
    text_h = sum(blank_h if not line else line_h for line, _ in TERMINAL)
    card_x0, card_x1, card_y0 = px(1290), px(1800), px(96)
    text_y0 = card_y0 + px(46) + px(24)
    card = (card_x0, card_y0, card_x1, text_y0 + text_h + px(20))

    d.rounded_rectangle(
        card,
        radius=px(18),
        fill=SURFACE + (235,),
        outline=LINE + (255,),
        width=max(1, s),
    )
    for cx, dot in zip(
        (card[0] + px(28), card[0] + px(50), card[0] + px(72)),
        ((34, 211, 238), (96, 165, 250), (71, 85, 105)),
    ):
        r = px(6)
        d.ellipse([cx - r, card[1] + px(24) - r, cx + r, card[1] + px(24) + r], fill=dot)
    d.line([(card[0], card[1] + px(46)), (card[2], card[1] + px(46))], fill=LINE, width=max(1, s))

    colors = {"prompt": GLOW_B, "value": INK, "muted": MUTED}
    ty = text_y0
    for line, kind in TERMINAL:
        if line:
            d.text((card[0] + px(30), ty), line, font=f_term, fill=colors[kind])
            ty += line_h
        else:
            ty += blank_h

    # -- bloco de texto principal ------------------------------------------
    x = px(PAD)
    d.text((x, px(72)), PROMPT, font=font("mono_bold", px(30)), fill=GLOW_B)

    f_name = font("bold", px(96))
    d.text((x, px(116)), NOME, font=f_name, fill=INK)

    # barra de acento sob o nome
    bar_y = px(248)
    bar_w = px(220)
    bar = linear_gradient(bar_w, px(6), GLOW_A, GLOW_B).convert("RGBA")
    img.alpha_composite(bar, (x, bar_y))

    d.text((x, px(272)), HEADLINE, font=font("medium", px(38)), fill=INK_DIM)

    # -- chips de tecnologia ------------------------------------------------
    f_chip = font("medium", px(27))
    chip_h, gap, padx = px(52), px(14), px(22)
    y0, y1 = px(362), px(362) + chip_h
    cx = x
    max_x = px(W - PAD)
    for label in CHIPS:
        cw = text_width(d, label, f_chip) + padx * 2
        if cx + cw > max_x:  # nunca estoura a margem
            break
        d.rounded_rectangle(
            [cx, y0, cx + cw, y1],
            radius=chip_h // 2,
            fill=(15, 23, 42, 200),
            outline=LINE + (255,),
            width=max(1, s),
        )
        tw = text_width(d, label, f_chip)
        d.text((cx + (cw - tw) // 2, y0 + chip_h // 2), label, font=f_chip, fill=(203, 213, 225), anchor="lm")
        cx += cw + gap

    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera o banner do perfil.")
    ap.add_argument("--scale", type=int, default=2, help="fator de supersampling (padrao 2)")
    ap.add_argument("--out", default="assets/banner.png", help="caminho de saida")
    args = ap.parse_args()

    img = build(max(1, args.scale))
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"ok: {out} ({img.width}x{img.height}, {os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
