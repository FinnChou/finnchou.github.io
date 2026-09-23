#!/usr/bin/env python3
"""通过 IndexNow 协议把 URL 主动推送给搜索引擎（Bing / Yandex / Seznam / Naver）。

相比等爬虫自己上门，IndexNow 是推模式，发完新文章跑一次就行。
Google 不支持该协议，它那边仍需走 Search Console。
CI 在每次部署完成后会以 --since 模式自动运行（见 .github/workflows/pages-deploy.yml）。

用法:
    python3 tools/indexnow_submit.py                    # 推送 sitemap 里的全部 URL
    python3 tools/indexnow_submit.py <url> [<url> ...]  # 只推送指定的 URL
    python3 tools/indexnow_submit.py --since=<rev>      # 只推送 <rev>..HEAD 间改动过的文章 / 页面
    python3 tools/indexnow_submit.py --dry              # 只打印将要提交的内容

前置条件：密钥文件必须已部署到线上且可访问，
即 https://finnchou.github.io/<KEY>.txt 返回 200 且内容就是 KEY。
"""

import json
import re
import subprocess
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

HOST = "finnchou.github.io"
KEY = "8301e9ec05d8bf01bb2173eb93b23c55"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP = f"https://{HOST}/sitemap.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"
UA = "Mozilla/5.0 (compatible; indexnow-submitter/1.0)"

SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

# 源文件 → 线上路径，须与 _config.yml 里的 permalink 一致（posts: /posts/:title/，tabs: /:title/）
SOURCE_ROUTES = [
    (re.compile(r"^_posts/(?:.*/)?\d{4}-\d{2}-\d{2}-(.+)\.(?:md|markdown)$"), "/posts/{}/"),
    (re.compile(r"^_tabs/(.+)\.md$"), "/{}/"),
]


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def urls_from_sitemap():
    root = ET.fromstring(fetch(SITEMAP))
    return [loc.text.strip() for loc in root.iter(f"{SM_NS}loc") if loc.text]


def urls_from_git_diff(base):
    """base..HEAD 之间新增、修改或删除的文章 / 页面对应的 URL。

    删掉的文章也要报：IndexNow 的约定是让搜索引擎回来抓一次，见到 404 后自行下架。
    --no-renames 把改名拆成「删旧 + 增新」，新旧两个地址都会提交。
    """
    out = subprocess.run(
        ["git", "-c", "core.quotepath=off", "diff", "--name-only", "--no-renames",
         base, "HEAD", "--", "_posts", "_tabs"],
        check=True, capture_output=True, text=True,
    ).stdout
    urls = []
    for path in out.splitlines():
        for pattern, route in SOURCE_ROUTES:
            m = pattern.match(path)
            if m:
                urls.append(f"https://{HOST}" + route.format(m.group(1)))
                break
    return urls


def verify_key():
    """密钥文件不可用时 IndexNow 会直接拒绝，先自检一遍省得白提交。"""
    try:
        body = fetch(KEY_LOCATION).decode("utf-8").strip()
    except urllib.error.HTTPError as e:
        return False, f"{KEY_LOCATION} 返回 HTTP {e.code}"
    except Exception as e:
        return False, f"{KEY_LOCATION} 无法访问: {e}"
    if body != KEY:
        return False, f"密钥文件内容不匹配: 期望 {KEY}，实际 {body!r}"
    return True, "密钥文件校验通过"


def submit(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=data, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


# IndexNow 的返回码含义，官方文档里散落各处，这里集中标注
STATUS_HINT = {
    200: "已接收",
    202: "已接收，密钥待验证",
    400: "请求格式有误",
    403: "密钥无效（密钥文件不可访问或内容不符）",
    422: "URL 与 host 不匹配，或密钥与站点不符",
    429: "提交过于频繁",
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    since = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--since=")), None)

    if since:
        urls = urls_from_git_diff(since)
        if not urls:
            # 只改了配置、脚本或图片的提交很常见，这不算失败
            print(f"{since}..HEAD 之间没有改动文章或页面，无需提交")
            return 0
    else:
        urls = args if args else urls_from_sitemap()
    bad = [u for u in urls if not u.startswith(f"https://{HOST}/")]
    if bad:
        print("以下 URL 不属于本站，已跳过：", file=sys.stderr)
        for u in bad:
            print("  ", u, file=sys.stderr)
        urls = [u for u in urls if u not in bad]
    if not urls:
        print("没有可提交的 URL"); return 1

    print(f"待提交 {len(urls)} 条 URL，前 3 条：")
    for u in urls[:3]:
        print("  ", u)

    if dry:
        print("\n--dry 模式，未实际提交")
        return 0

    ok, msg = verify_key()
    print(f"\n{msg}")
    if not ok:
        print("密钥未就绪，提交会被拒绝。请先确认该文件已部署上线。", file=sys.stderr)
        return 1

    status, body = submit(urls)
    hint = STATUS_HINT.get(status, "未知状态")
    print(f"\nIndexNow 返回: HTTP {status}（{hint}）")
    if body.strip():
        print("响应体:", body.strip()[:500])
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
