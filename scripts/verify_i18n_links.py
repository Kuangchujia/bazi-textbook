# -*- coding: utf-8 -*-
"""本地构建站内链接检查：按页面目录解析 href，区分目标为页面或静态资源。

判定：
- 外链（http/mailto/javascript/#/tel）不计。
- 绝对路径 /x/ → BUILD/x/index.html 或 BUILD/x（文件）。
- 相对路径相对当前 HTML 所在目录解析。
- 目标须在 BUILD 内存在（文件或 index.html）；否则记断链。
"""
import os, re, collections
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, '_i18n_work', 'build')
SKIP = ('404.html', 'google2ce2a6ce64face4e.html')


def resolve(base_dir, href):
    u = urlparse(href)
    if u.scheme or u.netloc or href.startswith(('#', '//', 'mailto:', 'javascript:', 'tel:')):
        return None
    p = u.path
    if not p:
        return None
    if p.startswith('/'):
        target = os.path.join(BUILD, p.lstrip('/'))
    else:
        target = os.path.join(base_dir, p)
    target = os.path.normpath(target)
    if not target.startswith(BUILD):
        return None
    cands = [target, os.path.join(target, 'index.html')]
    for c in cands:
        if os.path.isfile(c):
            return None
    return href


broken = collections.defaultdict(list)
pages = 0
hrefs = 0
for dp, dn, fs in os.walk(BUILD):
    for f in fs:
        if not f.endswith('.html') or f in SKIP:
            continue
        pages += 1
        fp = os.path.join(dp, f)
        h = open(fp, encoding='utf-8').read()
        for href in re.findall(r'(?:href|src)="([^"]+)"', h):
            hrefs += 1
            bad = resolve(dp, href)
            if bad:
                broken[os.path.relpath(fp, BUILD)].append(href)

nbad = sum(len(v) for v in broken.values())
print('pages', pages, 'hrefs', hrefs, 'broken', nbad, 'broken_pages', len(broken))
for k, v in list(sorted(broken.items()))[:15]:
    print(' ', k, '->', v[:4])
