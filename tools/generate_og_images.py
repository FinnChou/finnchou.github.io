#!/usr/bin/env python3
"""为每篇文章生成 1200x630 的社交预览图（og:image）。

用法:
    python3 tools/generate_og_images.py            # 生成全部
    python3 tools/generate_og_images.py --sample   # 只生成 3 张样例到 /tmp 预览
    python3 tools/generate_og_images.py --out DIR  # 指定输出目录

生成结果默认写入 assets/resource/og/<slug>.png，
slug 与文章 permalink 一致（文件名去掉日期前缀）。
"""

import argparse
import glob
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
MARGIN = 84

BG = (18, 20, 26)
BG_GLOW = (26, 30, 40)
TITLE_COLOR = (243, 244, 247)
META_COLOR = (138, 143, 155)
SITE_COLOR = (222, 224, 230)

# 每个分类一套强调色，让两个系列在信息流里能被一眼区分
CATEGORY_STYLE = {
    "数字信号处理": {"accent": (56, 189, 248), "motif": "wave"},
    "数字图像处理": {"accent": (167, 139, 250), "motif": "grid"},
    "色彩科学": {"accent": (251, 146, 60), "motif": "prism"},
}
DEFAULT_STYLE = {"accent": (148, 163, 184), "motif": "wave"}

# prism 纹样用的可见光谱锚点，长波在前——与出射光线偏折由小到大的顺序一致
SPECTRUM = [
    (255, 71, 60), (255, 138, 41), (255, 206, 61), (104, 214, 108),
    (58, 198, 219), (74, 132, 246), (154, 94, 235),
]


def spectrum_color(f):
    """在光谱锚点之间线性插值。f=0 取红端，f=1 取紫端。"""
    pos = f * (len(SPECTRUM) - 1)
    i = min(int(pos), len(SPECTRUM) - 2)
    t = pos - i
    a, b = SPECTRUM[i], SPECTRUM[i + 1]
    return tuple(int(round(a[c] + (b[c] - a[c]) * t)) for c in range(3))

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_FALLBACK = "/System/Library/Fonts/STHeiti Medium.ttc"

SITE_NAME = "Finn's blog"
# 用 U+00D7 而不是 U+2715：后者在部分中文字体里没有字形，会渲染成豆腐块
SITE_TAGLINE = "计算机视觉 × Camera"

# 标题横跨整幅宽度；装饰纹样只画在右下角（DECOR_X 以右、DECOR_Y 以下），
# 底部站点信息在左下角，三者互不重叠
DECOR_X = 700
DECOR_Y = 366


def load_font(size, bold=False):
    path = FONT_PATH if os.path.exists(FONT_PATH) else FONT_FALLBACK
    # Hiragino Sans GB.ttc 的 face 顺序：
    #   0 = W3, 1 = Interface W3, 2 = W6(粗), 3 = Interface W6
    index = 2 if bold else 0
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.truetype(path, size)


def text_width(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]


def wrap_title(draw, title, font, max_width):
    """中英混排换行：中文可任意断，英文尽量不拆词。"""
    lines, cur = [], ""
    token, i = "", 0
    while i < len(title):
        ch = title[i]
        # 英文/数字聚成一个不可拆分的 token
        if re.match(r"[A-Za-z0-9]", ch):
            token += ch
            i += 1
            continue
        if token:
            if cur and text_width(draw, cur + token, font) > max_width:
                lines.append(cur.rstrip())
                cur = token
            else:
                cur += token
            token = ""
        if text_width(draw, cur + ch, font) > max_width and cur.strip():
            lines.append(cur.rstrip())
            cur = "" if ch == " " else ch
        else:
            cur += ch
        i += 1
    if token:
        if cur and text_width(draw, cur + token, font) > max_width:
            lines.append(cur.rstrip())
            cur = token
        else:
            cur += token
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def fit_title(draw, title, max_width, max_lines=3):
    """字号自适应：长标题逐级缩小，保证不超过 max_lines 行。"""
    for size in (64, 58, 52, 46, 42):
        font = load_font(size, bold=True)
        lines = wrap_title(draw, title, font, max_width)
        if len(lines) <= max_lines:
            return font, lines, size
    font = load_font(42, bold=True)
    lines = wrap_title(draw, title, font, max_width)
    return font, lines[:max_lines], 42


def draw_background(img, style):
    """深色底 + 右上角柔光 + 与分类呼应的几何纹样。"""
    draw = ImageDraw.Draw(img, "RGBA")
    accent = style["accent"]

    # 右上角径向柔光，避免大面积纯色显得呆板
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy, r = W - 140, 120, 520
    for step in range(28, 0, -1):
        rr = int(r * step / 28)
        alpha = int(10 * (1 - step / 28) ** 1.6)
        gdraw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                      fill=BG_GLOW + (alpha,))
    img.alpha_composite(glow)

    if style["motif"] == "wave":
        # 正弦波：呼应信号处理。只画在右侧，并从左端淡入，避免抢标题的视觉重心
        for amp, period, alpha, yoff, width in (
                (48, 290, 64, 470, 3),
                (32, 206, 42, 512, 2),
                (19, 154, 27, 548, 2)):
            prev = None
            for x in range(DECOR_X, W + 1, 3):
                y = yoff + amp * math.sin((x - DECOR_X) / period * 2 * math.pi)
                if prev is not None:
                    # 越靠左越淡，右侧保持满强度
                    fade = min(1.0, (x - DECOR_X) / 240)
                    draw.line([prev, (x, y)],
                              fill=accent + (int(alpha * fade),), width=width)
                prev = (x, y)
    elif style["motif"] == "prism":
        # 棱镜色散：一束白光进三棱镜，散作可见光谱——「光与色」最经典的图景
        apex, bl, br = (852, 416), (777, 546), (927, 546)
        entry = ((apex[0] + bl[0]) / 2, (apex[1] + bl[1]) / 2)
        exit_pt = ((apex[0] + br[0]) / 2, (apex[1] + br[1]) / 2)

        # 入射白光：同样从左端淡入，与另外两种纹样的处理保持一致
        step = 4
        for x in range(DECOR_X, int(entry[0]), step):
            fade = min(1.0, (x - DECOR_X) / 150)
            draw.line([(x, entry[1]), (x + step, entry[1])],
                      fill=(238, 240, 246) + (int(126 * fade),), width=3)
        # 棱镜内部的光路
        draw.line([entry, exit_pt], fill=(238, 240, 246, 58), width=2)

        # 出射光谱：红偏折最小、紫最大，自出射点向右下张开成一片连续色带。
        # 逐像素着色而不是叠画多条光线——后者在交叠处 alpha 会迅速累积到饱和，
        # 亮度就再也压不下来了
        x0, y0 = exit_pt
        ang0, ang1 = math.radians(-2.0), math.radians(11.5)
        feather = math.radians(0.7)          # 扇形上下缘的羽化宽度
        reach = W - x0
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        px = layer.load()
        for X in range(int(x0), W):
            dx = X - x0
            for Y in range(DECOR_Y, H):
                ang = math.atan2(Y - y0, dx)
                if ang < ang0 - feather or ang > ang1 + feather:
                    continue
                edge = min(ang - (ang0 - feather), (ang1 + feather) - ang)
                aa = min(1.0, edge / feather)
                f = min(1.0, max(0.0, (ang - ang0) / (ang1 - ang0)))
                fade = 1 - 0.32 * min(1.0, math.hypot(dx, Y - y0) / reach)
                r, g, b = spectrum_color(f)
                px[X, Y] = (r, g, b, int(120 * fade * aa))
        img.alpha_composite(layer)

        # 棱镜轮廓压在光路之上
        for a, b in ((apex, bl), (bl, br), (br, apex)):
            draw.line([a, b], fill=accent + (96,), width=2)
    else:
        # 像素网格：呼应图像处理
        cell = 36
        gx0, gy0 = DECOR_X + 40, DECOR_Y
        cols = (W - gx0) // cell + 1
        rows = (H - gy0) // cell + 1
        # 先铺高亮格子，再压网格线，像被逐块处理过的图像
        for bx, by in [(2, 1), (5, 3), (8, 2), (3, 6), (10, 4),
                       (6, 7), (11, 1), (1, 9), (7, 10), (4, 11), (9, 8)]:
            x0, y0 = gx0 + bx * cell, gy0 + by * cell
            if x0 < W and y0 < H:
                draw.rectangle([x0, y0, x0 + cell, y0 + cell],
                               fill=accent + (24,))
        for c in range(cols):
            gx = gx0 + c * cell
            draw.line([(gx, gy0), (gx, H)], fill=accent + (14,), width=1)
        for r in range(rows):
            gy = gy0 + r * cell
            draw.line([(gx0, gy), (W, gy)], fill=accent + (14,), width=1)


def render(title, category, out_path):
    style = CATEGORY_STYLE.get(category, DEFAULT_STYLE)
    accent = style["accent"]

    img = Image.new("RGBA", (W, H), BG + (255,))
    draw_background(img, style)
    draw = ImageDraw.Draw(img)

    # 分类
    cat_font = load_font(26, bold=False)
    cat_y = 122
    draw.text((MARGIN, cat_y), category or "", font=cat_font, fill=accent)

    # 标题（自适应字号 + 换行），横跨整幅宽度
    max_width = W - MARGIN * 2 - 40
    title_font, lines, size = fit_title(draw, title, max_width)
    line_height = int(size * 1.36)
    title_y = 184
    y = title_y
    for line in lines:
        draw.text((MARGIN, y), line, font=title_font, fill=TITLE_COLOR)
        y += line_height

    # 左侧强调竖条：高度跟随分类 + 标题这一整块
    draw.rounded_rectangle(
        [MARGIN - 28, cat_y + 4, MARGIN - 20, y - line_height + size + 6],
        radius=4, fill=accent)

    # 底部分隔线（止于装饰区之前）+ 站点信息
    draw.line([(MARGIN, H - 132), (DECOR_X - 80, H - 132)],
              fill=(58, 62, 74), width=1)
    site_font = load_font(30, bold=True)
    tag_font = load_font(23, bold=False)
    draw.text((MARGIN, H - 106), SITE_NAME, font=site_font, fill=SITE_COLOR)
    draw.text((MARGIN, H - 64), SITE_TAGLINE, font=tag_font, fill=META_COLOR)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path, size, len(lines)


def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    fm = raw.split("---", 2)[1]
    m_title = re.search(r"^title:\s*(.+)$", fm, re.M)
    m_cat = re.search(r"^categories:\s*(.+)$", fm, re.M)
    title = m_title.group(1).strip().strip("\"'") if m_title else ""
    cat = m_cat.group(1).strip().strip("[]\"'") if m_cat else ""
    cat = cat.split(",")[0].strip().strip("\"'")
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(path))
    slug = re.sub(r"\.md$", "", slug)
    return title, cat, slug


def render_site(out_path):
    """站点级的社交预览图（_config.yml 的 social_preview_image）：
    三棱镜底纹，分类行列出三个系列并各用自己的强调色，标题为站名。"""
    style = CATEGORY_STYLE["色彩科学"]
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw_background(img, style)
    draw = ImageDraw.Draw(img)
    cat_font = load_font(26, bold=False)
    x, y = MARGIN, 122
    for i, (name, st) in enumerate(CATEGORY_STYLE.items()):
        if i:
            draw.text((x, y), "·", font=cat_font, fill=(90, 94, 108))
            x += draw.textlength("·", font=cat_font) + 14
        draw.text((x, y), name, font=cat_font, fill=st["accent"])
        x += draw.textlength(name, font=cat_font) + 14
    draw.text((MARGIN, 184), SITE_NAME, font=load_font(96, bold=True), fill=TITLE_COLOR)
    draw.text((MARGIN, 320), "计算机视觉、Camera 成像、色彩科学与数字图像处理的技术笔记",
              font=load_font(30, bold=False), fill=META_COLOR)
    draw.rounded_rectangle([MARGIN - 28, 126, MARGIN - 20, 300], radius=4, fill=style["accent"])
    draw.line([(MARGIN, H - 132), (DECOR_X - 80, H - 132)], fill=(58, 62, 74), width=1)
    draw.text((MARGIN, H - 106), SITE_NAME, font=load_font(30, bold=True), fill=SITE_COLOR)
    draw.text((MARGIN, H - 64), "finnchou.github.io", font=load_font(23, bold=False), fill=META_COLOR)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true",
                    help="只生成 3 张样例用于预览")
    ap.add_argument("--site", action="store_true",
                    help="只生成站点级的社交预览图 site-preview.png")
    ap.add_argument("--out", default="assets/resource/og",
                    help="输出目录")
    args = ap.parse_args()

    if args.site:
        out = render_site(os.path.join(args.out, "site-preview.png"))
        print(f"{out}  {os.path.getsize(out) / 1024:.0f}KB")
        return

    posts = sorted(glob.glob("_posts/*.md"))
    if args.sample:
        # 挑最短、最长、以及另一个分类各一篇，覆盖排版边界
        parsed = [(p,) + parse_post(p) for p in posts]
        parsed.sort(key=lambda x: len(x[1]))
        picks = [parsed[0], parsed[-1]]
        for item in parsed:
            if item[2] != picks[0][2]:
                picks.insert(1, item)
                break
        posts = [p[0] for p in picks]

    count = 0
    for p in posts:
        title, cat, slug = parse_post(p)
        if not title:
            print(f"跳过（无标题）: {p}", file=sys.stderr)
            continue
        out, size, nlines = render(title, cat, os.path.join(args.out, slug + ".png"))
        kb = os.path.getsize(out) / 1024
        print(f"{slug:<46} {size}px/{nlines}行  {kb:5.0f}KB")
        count += 1
    print(f"\n共生成 {count} 张 → {args.out}")


if __name__ == "__main__":
    main()
