# -*- coding: utf-8 -*-
"""导出十七课为 Markdown（供术数仓库开源）。仅抽正文，不增改一个字。

输出目录：book/geju_source/open_bazi_repo/lessons/
"""
import os, re, html, json
from bs4 import BeautifulSoup
import _wpq

OUT = os.path.join(os.path.dirname(__file__), 'open_bazi_repo')
LES = os.path.join(OUT, 'lessons')
os.makedirs(LES, exist_ok=True)

LESSONS = [(227, 1, '概论'), (228, 2, '阴阳五行'), (229, 3, '天干及五合'),
           (230, 4, '地支'), (232, 5, '地支关系'), (233, 6, '八字排法'),
           (234, 7, '长生十二宫'), (235, 8, '十神排法'), (236, 9, '十神类象'),
           (237, 10, '十神组合（一）· 格局框架与分析方法'),
           (238, 11, '十神组合（二）· 四吉神配合'),
           (239, 12, '十神组合（三）· 四凶神制化'),
           (240, 13, '学业、事业、婚姻 · 十神实战'),
           (241, 14, '旺衰抑扶的基本概念'), (242, 15, '旺衰的用法'),
           (243, 16, '神煞'), (244, 17, '大运流年的看法')]


def txt(node):
    return re.sub(r'\s+', ' ', node.get_text(' ', strip=True)).strip()


def conv(node, depth=0):
    """把 DOM 节点转成 Markdown 行列表。"""
    out = []
    for ch in node.children:
        if getattr(ch, 'name', None) is None:
            t = str(ch).strip()
            if t:
                out.append(t)
            continue
        n = ch.name
        if n in ('style', 'script', 'nav'):
            continue
        if n in ('h1', 'h2', 'h3', 'h4'):
            lv = int(n[1])
            out.extend(['', '#' * lv + ' ' + txt(ch), ''])
        elif n == 'p':
            s = txt(ch)
            if s:
                out.extend([s, ''])
        elif n in ('ul', 'ol'):
            for i, li in enumerate(ch.find_all('li', recursive=False), 1):
                prefix = '- ' if n == 'ul' else '%d. ' % i
                out.append(prefix + txt(li))
            out.append('')
        elif n == 'blockquote':
            for p in ch.find_all(['p', 'li']):
                s = txt(p)
                if s:
                    out.append('> ' + s)
            out.append('')
        elif n == 'pre':
            out.extend(['```', ch.get_text().strip('\n'), '```', ''])
        elif n == 'details':
            s = ch.find('summary')
            if s:
                out.append('**' + txt(s) + '**')
                out.append('')
            inner = BeautifulSoup(''.join(str(c) for c in ch.contents[1:]), 'html.parser')
            out.extend(conv(inner, depth + 1))
        elif n == 'table':
            rows = ch.find_all('tr')
            for i, tr in enumerate(rows):
                cells = [txt(c) for c in tr.find_all(['th', 'td'])]
                out.append('| ' + ' | '.join(cells) + ' |')
                if i == 0:
                    out.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
            out.append('')
        elif n == 'hr':
            out.extend(['---', ''])
        elif n == 'br':
            out.append('  ')
        elif n == 'a':
            out.append('[%s](%s)' % (txt(ch), ch.get('href', '')))
        elif n == 'img':
            out.append('![%s](%s)' % (ch.get('alt', ''), ch.get('src', '')))
        else:
            out.extend(conv(ch, depth + 1))
    return out


def main():
    manifest = []
    for pid, no, title in LESSONS:
        s, d = _wpq.call('/wp/v2/pages/%d?context=edit&_fields=content,modified,link' % pid)
        assert s == 200, pid
        soup = BeautifulSoup(d['content']['raw'], 'html.parser')
        page = soup.select_one('.jy-page') or soup
        for bad in page.select('style, script, nav.jy-toc'):
            bad.decompose()
        body = conv(page)
        lines = [l.rstrip() for l in body]
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
        fn = 'lesson-%02d.md' % no
        with open(os.path.join(LES, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        manifest.append({'no': no, 'file': fn, 'title': title,
                         'source': d['link'], 'modified': d['modified'],
                         'chars': len(text)})
        print('%02d %s %d 字' % (no, fn, len(text)))
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('合计', sum(x['chars'] for x in manifest), '字')


if __name__ == '__main__':
    main()
