# -*- coding: utf-8 -*-
"""r62 Q1：给四语 19 页/语（共 76 页）的 frontmatter 注入本语 title。

title 取值＝该页 H1 原文（本语），不改正文、不改 H1、不改 URL／canonical／hreflang。
幂等：若已有 title: 行则按 H1 校正；无则在 lang: 行后插入。
备份在 _i18n_work/bak_r62_titles/。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
LANGS = ['en', 'ja', 'ko', 'zh-hant']

APPLY = '--apply' in sys.argv


def targets(lang):
    files = ['textbook/L%02d.%s.md' % (i, lang) for i in range(1, 18)]
    files += ['exercises/README.%s.md' % lang]
    files += ['exercises/exercises.%s.md' % lang]
    return files


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


changed = 0
for lang in LANGS:
    for rel in targets(lang):
        fp = os.path.join(DOCS, rel)
        if not os.path.isfile(fp):
            print('MISSING', rel)
            continue
        s = open(fp, encoding='utf-8').read()
        m = re.search(r'^#\s+(.+)$', s, re.M)
        if not m:
            print('NO H1', rel)
            continue
        h1 = m.group(1).strip()
        new_title = 'title: "%s"' % esc(h1)
        lines = s.split('\n')
        out_lines = []
        done = False
        for line in lines:
            if line.startswith('title:'):
                out_lines.append(new_title)
                done = True
            else:
                out_lines.append(line)
                if not done and line.strip() == 'lang: %s' % lang:
                    out_lines.append(new_title)
                    done = True
        if not done:
            print('INJECT FAILED', rel)
            continue
        out = '\n'.join(out_lines)
        if APPLY:
            with open(fp, 'w', encoding='utf-8', newline='\n') as f:
                f.write(out)
        print(('APPLY' if APPLY else 'DRY '), rel, '->', h1[:50])
        changed += 1

print('total changed', changed, '(apply)' if APPLY else '(dry)')
