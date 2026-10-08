#!/usr/bin/env python3
"""
Utilitarios visuais compartilhados pelos geradores de imagem do perfil
(make_banner.py e make_stats.py): fontes, gradientes, brilho e cartoes.

Manter isso num modulo so garante que o banner e os cards tenham
exatamente a mesma paleta e o mesmo acabamento.
"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ paleta ---
BG_A = (9, 14, 26)          # fundo, canto superior esquerdo
BG_B = (17, 24, 42)         # fundo, canto inferior direito
GLOW_A = (37, 99, 235)      # azul
GLOW_B = (34, 211, 238)     # ciano
INK = (248, 250, 252)       # texto principal
INK_DIM = (148, 163, 184)   # texto secundario
MUTED = (125, 140, 163)     # texto terciario
LINE = (30, 41, 59)         # bordas
SURFACE = (13, 19, 33)      # superficie dos cartoes

FONT_CANDIDATES = {
    "bold": [
        "~/.local/share/fonts/FiraSans-Bold.ttf",
        "/usr/share/fonts/truetype/fira/FiraSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "semibold": [
        "~/.local/share/fonts/FiraSans-SemiBold.ttf",
        "/usr/share/fonts/truetype/fira/FiraSans-SemiBold.ttf",
        "~/.local/share/fonts/FiraSans-Bold.ttf",
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
    """Carrega a primeira fonte disponivel, com erro claro se nenhuma existir."""
    for path in FONT_CANDIDATES[kind]:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(
        f"Nenhuma fonte encontrada para '{kind}'. Edite FONT_CANDIDATES em assets/cardkit.py."
    )


def linear_gradient(w: int, h: int, c0, c1) -> Image.Image:
    """Gradiente diagonal suave entre duas cores."""
    t = (np.add.outer(np.linspace(0, 1, h), np.linspace(0, 1, w)) / 2.0)[..., None]
    c0a, c1a = np.array(c0, float), np.array(c1, float)
    return Image.fromarray((c0a + (c1a - c0a) * t).astype(np.uint8), "RGB")


def radial_glow(w: int, h: int, cx: float, cy: float, radius: float) -> Image.Image:
    """Mascara de brilho radial (0-255)."""
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xs - cx) / radius) ** 2 + ((ys - cy) / radius) ** 2)
    a = np.clip(1.0 - d, 0.0, 1.0) ** 1.8
    return Image.fromarray((a * 255).astype(np.uint8), "L")


def add_glow(img: Image.Image, cx: float, cy: float, radius: float, color, alpha: float) -> Image.Image:
    """Aplica um brilho radial colorido sobre a imagem (RGB)."""
    glow = Image.new("RGB", img.size, color)
    mask = radial_glow(img.width, img.height, cx, cy, radius).point(lambda v: int(v * alpha))
    return Image.composite(glow, img, mask)


def text_width(draw: ImageDraw.ImageDraw, s: str, f: ImageFont.FreeTypeFont) -> int:
    return int(draw.textlength(s, font=f))


def rounded_mask(size: tuple[int, int], radius: int, supersample: int = 4) -> Image.Image:
    """Mascara de canto arredondado com borda suave (antialiasing)."""
    w, h = size
    m = Image.new("L", (w * supersample, h * supersample), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, w * supersample - 1, h * supersample - 1], radius * supersample, fill=255
    )
    return m.resize((w, h), Image.LANCZOS)


def make_card(w: int, h: int, radius: int = 16, scale: int = 2):
    """
    Cria um cartao no mesmo estilo do banner.

    Retorna (imagem, draw) numa resolucao `scale`x maior para desenhar com
    nitidez; finalize com `finish_card()`.
    """
    img = linear_gradient(w * scale, h * scale, BG_A, BG_B)
    img = add_glow(img, w * scale * 0.05, h * scale * 0.10, w * scale * 1.1, GLOW_A, 0.26)
    img = add_glow(img, w * scale * 1.05, h * scale * 1.10, w * scale * 0.75, GLOW_B, 0.14)
    return img, ImageDraw.Draw(img)


def finish_card(img: Image.Image, w: int, h: int, radius: int = 16, scale: int = 2) -> Image.Image:
    """Reduz para o tamanho final, aplica cantos transparentes e a borda."""
    small = img.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(small, (0, 0), rounded_mask((w, h), radius))
    ImageDraw.Draw(out).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius, outline=LINE + (255,), width=1
    )
    return out
