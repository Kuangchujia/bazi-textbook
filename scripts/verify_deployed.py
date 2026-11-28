#!/usr/bin/env python3
"""线上五语发布验收：对 bazi-textbook.jiayanyide.com 实测关键 SEO/GEO 标记。

只读，不改任何文件。用法：python scripts/verify_deployed.py
"""
import re
import urllib.request
import urllib.error

BASE = "https://bazi-textbook.jiayanyide.com"
LANGS = ["", "en/", "zh-hant/", "ja/", "ko/"]
EXPECT_TITLE = {
    "": "四柱八字基础教材",
    "en/": "Four Pillars BaZi Foundation Course",
    "zh-hant/": "四柱八字基礎教材",
    "ja/": "四柱八字基礎教材",
    "ko/": "사주팔자 기초 교재",
}
EXPECT_LANG = {"": "zh", "en/": "en", "zh-hant/": "zh-Hant", "ja/": "ja", "ko/": "ko"}
EXPECT_OG = {"": "zh_CN", "en/": "en_US", "zh-hant/": "zh_TW", "ja/": "ja_JP", "ko/": "ko_KR"}


def fetch(path, timeout=20):
    url = BASE + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "i18n-acceptance/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", url
    except Exception as e:
        return 0, "", str(e)


def one(pattern, html):
    m = re.search(pattern, html, re.S | re.I)
    return m.group(1).strip() if m else ""


fails = []
print("== 五语首页 ==")
for lang in LANGS:
    path = "/" + lang
    code, html, final = fetch(path)
    title = one(r"<title>(.*?)</title>", html)
    hlang = one(r'<html[^>]+lang="([^"]+)"', html)
    og = one(r'<meta[^>]+property="og:locale"[^>]+content="([^"]+)"', html)
    xd = html.count('hreflang="x-default"')
    canon = one(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)
    n_href = html.count("hreflang=")
    ld = one(r'"inLanguage"\s*:\s*"([^"]+)"', html)
    ok = (
        code == 200
        and EXPECT_TITLE[lang] in title
        and hlang == EXPECT_LANG[lang]
        and og == EXPECT_OG[lang]
        and xd == 1
        and canon.rstrip("/") == BASE + path.rstrip("/")
        and n_href >= 10
    )
    print(f"{path:12} HTTP{code} title={title[:45]!r} lang={hlang} og={og} xd={xd} href={n_href} canon={canon[-40:]!r} ld={ld}")
    print("   ", "PASS" if ok else "FAIL")
    if not ok:
        fails.append(path)

print("\n== 代表课页 ==")
for lang in LANGS:
    path = "/" + lang + "textbook/L01/"
    code, html, final = fetch(path)
    title = one(r"<title>(.*?)</title>", html)
    xd = html.count('hreflang="x-default"')
    h1 = one(r"<h1[^>]*>(.*?)</h1>", html)
    h1 = re.sub(r"<[^>]+>", "", h1).strip()
    ok = code == 200 and xd == 1 and "第1课" not in title and "第1課" not in title if lang == "en/" else code == 200 and xd == 1
    print(f"{path:28} HTTP{code} xd={xd} title={title[:55]!r} H1={h1[:30]!r} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        fails.append(path)

print("\n== 繁中死链 / 外链 rel ==")
code, html, _ = fetch("/zh-hant/textbook/L01/")
rel_left = len(re.findall(r'href="/bazi/', html))
abs_n = len(re.findall(r'href="https://jiayanyide.com/bazi/', html))
print(f"zh-hant L01: relative /bazi/ = {rel_left} (expect 0), absolute = {abs_n} (expect >0)")
if rel_left or not abs_n:
    fails.append("zh-hant L01 links")
for lang in LANGS:
    code, html, _ = fetch("/" + lang)
    m = re.search(r"<h2[^>]*>相关站点</h2>", html) or re.search(r"<h2[^>]*>Related sites</h2>", html) or re.search(r"<h2[^>]*>関連サイト</h2>", html) or re.search(r"<h2[^>]*>관련 사이트</h2>", html) or re.search(r"<h2[^>]*>相關站點</h2>", html)
    seg = html[m.end():html.find("<h2", m.end())] if m else ""
    n = seg.count('rel="noopener noreferrer"')
    print(f"{('/'+lang):12} related-sites rel count = {n}")
    if m and n == 0:
        fails.append("rel " + lang)

print("\n== 机器文件 ==")
for p in ["/sitemap.xml", "/llms.txt", "/llms-full.txt", "/index.json"]:
    code, html, _ = fetch(p)
    print(f"{p:16} HTTP{code} bytes={len(html)}")
    if code != 200:
        fails.append(p)

print("\n== 结论 ==")
print("FAILS:", fails if fails else "NONE — 线上五语验收全部通过")
