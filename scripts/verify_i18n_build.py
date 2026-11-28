# -*- coding: utf-8 -*-
"""五语教材站本地构建验收：SEO 标记、站级页译文、题数、原文哈希。"""
import os, re, json, hashlib, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, '_i18n_work', 'build')
SITE = 'https://bazi-textbook.jiayanyide.com/'
LANG = {'': 'zh', 'zh-hant/': 'zh-hant', 'en/': 'en', 'ja/': 'ja', 'ko/': 'ko'}
CAN = re.compile(r'<link rel="canonical" href="([^"]+)"')
HRE = re.compile(r'<link rel="alternate" href="([^"]+)" hreflang="([^"]+)"')
HL = re.compile(r'<html[^>]*lang="([^"]+)"')
OG = re.compile(r'og:locale" content="([^"]+)"')
LD = re.compile(r'"inLanguage": "([^"]+)"')

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
            hl = HL.findall(h)
            og = OG.findall(h)
            ld = LD.findall(h)
            bad = []
            if not can or can[0].rstrip('/') != url.rstrip('/'):
                bad.append('CANON')
            if len(set(x[1] for x in hre)) != 5:
                bad.append('HREFLANG')
            if not hl:
                bad.append('LANG')
            if not og:
                bad.append('OG')
            if not ld:
                bad.append('LD')
            rows.append(dict(url=url, lang=lang, flags=bad))

bad = [r for r in rows if r['flags']]
print('pages', len(rows), 'by lang', dict(collections.Counter(r['lang'] for r in rows)))
print('SEO fails', len(bad))
for r in bad[:12]:
    print(' ', r['url'], r['flags'])
json.dump(rows, open(os.path.join(ROOT, '_i18n_work', 'seo_audit.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# 站级页译文检查：正文不得含简中特有简体字形串（对四语页）
checks = ['一体多面', '简体中文', '练习题手册', '版权与版本说明', '课程与教学服务']
for lang in ['en', 'ja', 'ko', 'zh-hant']:
    hits = []
    for pre, lg in LANG.items():
        if lg != lang:
            continue
        for dp, dn, fs in os.walk(os.path.join(BUILD, pre)):
            for f in fs:
                if not f.endswith('.html'):
                    continue
                h = open(os.path.join(dp, f), encoding='utf-8').read()
                body = h.split('<article', 1)[-1] if '<article' in h else h
                for c in checks:
                    if c in body:
                        hits.append((f, c))
    print(lang, 'simplified-leftovers', len(hits), hits[:6])

# 题数
for lang in ['zh', 'zh-hant', 'en', 'ja', 'ko']:
    pre = '' if lang == 'zh' else lang + '/'
    fp = os.path.join(BUILD, pre, 'exercises', 'exercises', 'index.html')
    if not os.path.exists(fp):
        print(lang, 'exercises MISSING')
        continue
    h = open(fp, encoding='utf-8').read()
    qs = len(re.findall(r'<h3[^>]*>', h))  # 期望 63
    print(lang, 'exercise h3', qs)

# 原文哈希
bad = 0
sums = open(os.path.join(ROOT, 'SHA256SUMS.txt'), encoding='utf-8').read().strip().splitlines()
for line in sums:
    h, rest = line.split('  ', 1)
    p = rest.split(' (')[0]
    cur = hashlib.sha256(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()
    if cur != h:
        bad += 1
        print('HASH MISMATCH', p)
print('frozen lessons', len(sums), 'mismatch', bad)
