#!/usr/bin/env python3
"""检查公式有没有在 Markdown 这一步被 kramdown 改坏。

本站行内公式用单个 $，但 kramdown 只认 $$：单 $ 里的内容会先被当成普通
Markdown 解析一遍，再交给浏览器端的 MathJax。由此产生四类问题：

  源码检查（_posts、_tabs）
    1. 单 $ 公式里的 \\{ \\} \\| \\! \\\\ \\: 等，反斜杠会被 kramdown 吃掉。
       \\{x\\} 变成 {x}，MathJax 照样排版、不报错，只是花括号没了。

  构建结果检查（_site 里开了 math 的页面）
    2. 单 $ 公式里混进 <em>/<strong>：公式里的 * 或 }_{ 被当成强调符号配了对，
       两处之间整段变斜体。
    3. 一段里 $ 的个数为奇数：公式被拆散，常见于段首 |x| 被当成表格。
    4. 表格外出现 \\( ：块级 $$ 前后缺空行，被当成段内公式排进了正文行。

写法约定（照此写就不会触发上面的检查）：
    - 上标星号写 ^{\\ast}，如 L^{\\ast}a^{\\ast}b^{\\ast}；不能写 ^\\ast（\\asta 会被读成一个命令）
    - }_{ 形式的下标写 }\\_{，如 \\overline{x}\\_{10}；Y_n 这种字母夹着的 _ 没事
    - 花括号、范数等需要反斜杠的写法，挪到 $$ 块级公式里，或换成 \\lbrace \\rbrace \\Vert
    - 块级 $$ 前后都留空行；表格单元格里只能用 $$（kramdown 会输出为行内）

用法:
    python3 tools/check_math.py            # 检查源码与 _site（需先 jekyll build）
    python3 tools/check_math.py <site_dir>
"""

import glob
import html
import os
import re
import sys

SOURCE_GLOBS = ["_posts/*.md", "_tabs/*.md"]

# kramdown 的可转义字符（kramdown/parser/kramdown/escaped_chars.rb）。
# \_ 与 \* 是本站有意用来躲开强调符号的转义，不算问题。
KRAMDOWN_ESCAPABLE = set("\\.*_+`<>()[]{}#!:|\"'$=-")
INTENDED_ESCAPES = {"_", "*"}

INLINE_MATH = re.compile(r"(?<![\\$])\$(?!\$)((?:\\[\s\S]|[^$\\])+?)\$")
BLOCK_TAGS = re.compile(
    r"</?(?:p|li|td|th|tr|h[1-6]|blockquote|div|ul|ol|table|thead|tbody|figure|figcaption|img|br|hr)\b[^>]*>")


def blank_out(m):
    """把匹配到的部分替换成等长空白，保留换行，这样后面还能报出正确的行号。"""
    return re.sub(r"[^\n]", " ", m.group(0))


def check_source(path):
    text = open(path, encoding="utf-8").read()
    # kramdown 会原样保护的部分不用查：front matter、代码块、行内代码、$$ 公式
    text = re.sub(r"\A---\n.*?\n---\n", blank_out, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1", blank_out, text, flags=re.S | re.M)
    text = re.sub(r"`[^`\n]+`", blank_out, text)
    text = re.sub(r"\$\$.*?\$\$", blank_out, text, flags=re.S)

    problems = []
    for m in INLINE_MATH.finditer(text):
        span = m.group(1)
        if re.search(r"\n\s*\n", span):  # 跨段落，说明是配错了对，交给构建结果检查
            continue
        eaten = sorted({e for e in re.findall(r"\\(.)", span)
                        if e in KRAMDOWN_ESCAPABLE and e not in INTENDED_ESCAPES})
        if eaten:
            line = text.count("\n", 0, m.start()) + 1
            marks = " ".join("\\" + e for e in eaten)
            problems.append(f"{path}:{line}: 单 $ 公式里的 {marks} 会被 kramdown 吃掉反斜杠："
                            f"${span.strip()[:60]}$")
    return problems


def page_source(page):
    """posts/<slug>/index.html → _posts/*-<slug>.md，找不到就原样返回页面路径。"""
    m = re.match(r"posts/([^/]+)/index\.html$", page)
    hits = glob.glob(f"_posts/*-{m.group(1)}.md") if m else []
    return hits[0] if hits else page


def check_page(site, page):
    raw = open(os.path.join(site, page), encoding="utf-8").read()
    if "tex-chtml.js" not in raw:  # 没开 math 的页面，$ 本来就不会被排版
        return []
    m = re.search(r'<div class="content">(.*?)</article>', raw, re.S)
    if not m:
        return []
    body = re.sub(r"<(pre|code|script|style)\b.*?</\1>", "", m.group(1), flags=re.S)
    where = page_source(page)
    problems = []

    for m in re.finditer(r"\\\((.{0,40})", re.sub(r"<table\b.*?</table>", "", body, flags=re.S)):
        problems.append(f"{where}: 块级 $$ 前后缺空行，被排成了行内公式：\\({html.unescape(m.group(1)).strip()}")

    body = re.sub(r"\\\(.*?\\\)|\\\[.*?\\\]", "", body, flags=re.S)  # kramdown 已接管的 $$ 公式
    for chunk in BLOCK_TAGS.split(body):
        text = html.unescape(re.sub(r"<[^>]+>", "", chunk))
        if len(re.findall(r"(?<!\\)\$", text)) % 2:
            problems.append(f"{where}: 一段里 $ 的个数为奇数，公式被拆散了：{text.strip()[:60]}")
            continue
        for span in INLINE_MATH.findall(chunk):
            if re.search(r"</?(?:em|strong|a|sub|sup)\b", span):
                problems.append(f"{where}: 公式里的 * 或 _ 被当成了强调符号：${html.unescape(span).strip()[:80]}$")
    return problems


def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "_site"
    if not os.path.isdir(site):
        print(f"{site} 不存在，请先 jekyll build", file=sys.stderr)
        return 2

    problems = []
    for pattern in SOURCE_GLOBS:
        for path in sorted(glob.glob(pattern)):
            problems += check_source(path)
    pages = sorted(os.path.relpath(p, site) for p in glob.glob(f"{site}/**/index.html", recursive=True))
    for page in pages:
        problems += check_page(site, page)

    for p in problems:
        print(p)
    if problems:
        print(f"\n共 {len(problems)} 处公式问题，写法约定见 tools/check_math.py 开头的说明")
        return 1
    print(f"公式检查通过（{len(pages)} 个页面）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
