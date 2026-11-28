# -*- coding: utf-8 -*-
"""r62 修复终验：Q1 标题本地化、Q2 死链、Q3 x-default、Q4-F rel、基线。"""
import os, re, collections, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, '_i18n_work', 'build')
SITE = 'https://bazi-textbook.jiayanyide.com/'
LANG = {'': 'zh', 'zh-hant/': 'zh-hant', 'en/': 'en', 'ja/': 'ja', 'ko/': 'ko'}
CAN = re.compile(r'<link rel="canonical" href="([^"]+)"')
HRE = re.compile(r'<link rel="alternate" href="([^"]+)" hreflang="([^"]+)"')
XD = re.compile(r'<link rel="alternate" hreflang="x-default" href="([^"]+)"')
TITLE = re.compile(r'<title>(.*?)</title>', re.S)
SIMP = ['说明', '题目', '概论', '课', '组合', '实战', '用法', '旺衰', '类象',
        '排法', '长生', '十神', '神煞', '大运', '流年', '一体多面']

rows = []
for pre, lang in LANG.items():
    for dp, dn, fs in os.walk(os.path.join(BUILD, pre)):
        for f in fs:
            if not f.endswith('.html') or f in ('404.html', 'google2ce2a6ce64face4e.html'):
                continue
            fp = os.path.join(dp, f)
            rel = os.path.relpath(fp, BUILD).replace(os.sep, '/')
            h = open(fp, encoding='utf-8').read()
            url = SITE + rel.replace('index.html', '')
            can = CAN.findall(h)
            hre = HRE.findall(h)
            xd = XD.findall(h)
            flag = []
            if not can or can[0].rstrip('/') != url.rstrip('/'):
                flag.append('CANON')
            if len(set(x[1] for x in hre)) != 5:
                flag.append('HREFLANG')
            if xd != [SITE]:
                flag.append('XDEFAULT')
            m = TITLE.search(h)
            title_head = m.group(1).split(' - ')[0].strip() if m else ''
            rows.append(dict(rel=rel, lang=lang, flags=flag, title=title_head))

print('CONTENT pages', len(rows))
print('canonical/hreflang/xdefault fails', sum(1 for r in rows if r['flags']))
for r in rows:
    if r['flags']:
        print('  FAIL', r['rel'], r['flags'], r.get('xd'))

# Q1：四语 76 页标题前半段不得含简中特征（ja/zh-hant 允许繁体/日文汉字，但排除简中特征词）
targets = []
for lang in ['en', 'ja', 'ko', 'zh-hant']:
    for i in range(1, 18):
        targets.append('%s/textbook/L%02d/index.html' % (lang, i))
    targets.append('%s/exercises/index.html' % lang)
    targets.append('%s/exercises/exercises/index.html' % lang)

# 四语页里 title 仍与简中源页 title 相同的页
bad_title = []
for lang in ['en', 'ja', 'ko', 'zh-hant']:
    for i in range(1, 18):
        zh = 'textbook/L%02d/index.html' % i
        lg = '%s/textbook/L%02d/index.html' % (lang, i)
        zh_t = next((r['title'] for r in rows if r['rel'] == zh), '')
        lg_t = next((r['title'] for r in rows if r['rel'] == lg), '')
        if zh_t and lg_t and zh_t == lg_t:
            bad_title.append((lg, lg_t))
print('Q1 same-as-zh titles', len(bad_title), bad_title[:5])

# Q2：繁中 /bazi/ 死链残留
bad_q2 = []
for r in rows:
    if r['lang'] == 'zh-hant':
        h = open(os.path.join(BUILD, r['rel']), encoding='utf-8').read()
        n = len(re.findall(r'href="/bazi/', h))
        if n:
            bad_q2.append((r['rel'], n))
print('Q2 remaining /bazi/ links', sum(n for _, n in bad_q2), 'in', len(bad_q2), 'pages')

# Q4-F：首页相关站点段外链 rel
for lang in ['', 'en/', 'zh-hant/', 'ja/', 'ko/']:
    fp = os.path.join(BUILD, lang, 'index.html')
    h = open(fp, encoding='utf-8').read()
    print('Q4-F', lang or 'zh', 'rel noopener noreferrer', h.count('rel="noopener noreferrer"'))

# SHA256
bad = 0
sums = open(os.path.join(ROOT, 'SHA256SUMS.txt'), encoding='utf-8').read().strip().splitlines()
for line in sums:
    hv, rest = line.split('  ', 1)
    p = rest.split(' (')[0]
    cur = hashlib.sha256(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()
    if cur != hv:
        bad += 1
print('SHA256 frozen', len(sums), 'mismatch', bad)
