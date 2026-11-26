# -*- coding: utf-8 -*-
"""练习题手册（不给答案）：逐课照录教材「练习」小节，删去折叠答案。

输出：book/geju_source/open_bazi_repo/练习题手册·无答案.md
"""
import os, re
from bs4 import BeautifulSoup
import _wpq

OUT = os.path.join(os.path.dirname(__file__), 'open_bazi_repo', '练习题手册·无答案.md')
LESSONS = [(227, 1, '概论'), (228, 2, '阴阳五行'), (229, 3, '天干及五合'),
           (230, 4, '地支'), (232, 5, '地支关系'), (233, 6, '八字排法'),
           (234, 7, '长生十二宫'), (235, 8, '十神排法'), (236, 9, '十神类象'),
           (237, 10, '十神组合（一）'), (238, 11, '十神组合（二）'),
           (239, 12, '十神组合（三）'), (240, 13, '十神实战'),
           (241, 14, '旺衰抑扶的基本概念'), (242, 15, '旺衰的用法'),
           (243, 16, '神煞'), (244, 17, '大运流年的看法')]


def clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def extract(raw):
    """返回 (题干 Markdown, 题数, 删除的答案块数)。"""
    # 只取「练习」h2 到下一个 h2 之间
    m = re.search(r'<h2([^>]*)>(?:课后)?练习</h2>(.*?)(?=<h2)', raw, re.S)
    if not m:
        return '', 0, 0, ''
    a = re.search(r'id="([^"]+)"', m.group(1))
    anchor = a.group(1) if a else ''
    seg = m.group(2)
    n_ans = len(re.findall(r'<details>', seg))
    seg = re.sub(r'<details>.*?</details>', '', seg, flags=re.S)
    seg = re.sub(r'<br\s*/?>', '\n', seg, flags=re.I)
    soup = BeautifulSoup(seg, 'html.parser')
    lines = []
    n_q = 0
    for ch in soup.children:
        if getattr(ch, 'name', None) is None:
            t = clean(str(ch))
            if t:
                lines.append(t)
        elif ch.name in ('h3', 'h4'):
            n_q += 1
            lines.extend(['', '### ' + clean(ch.get_text()), ''])
        elif ch.name == 'p':
            t = '\n'.join(clean(x) for x in ch.get_text('').split('\n') if clean(x))
            if not t or re.match(r'^(答案|正确答案|参考答案)', t):
                continue
            lines.extend([t, ''])
        elif ch.name in ('ol', 'ul'):
            for i, li in enumerate(ch.find_all('li', recursive=False), 1):
                lines.append(('- ' if ch.name == 'ul' else '%d. ' % i) + clean(li.get_text(' ', strip=True)))
            lines.append('')
        elif ch.name == 'blockquote':
            for p in ch.find_all(['p', 'li']):
                t = clean(p.get_text(' ', strip=True))
                if t:
                    lines.append('> ' + t)
            lines.append('')
    text = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()
    return text, n_q, n_ans, anchor


def main():
    parts = [
        '# 四柱八字基础教材十七课 · 练习题手册（无答案）\n',
        '## 使用说明\n',
        '本手册按课次照录《四柱八字基础教材》十七课公开页面「练习」小节的题干，未改字、未另编题。',
        '教材原有折叠答案一律不收；原题没有答案的，本手册也不补。',
        '需要核对出处时，按每课标题下的原文地址回查。',
        '本站只提供学术讨论，不涉及具体吉凶占卜。\n',
    ]
    total_q = total_a = 0
    missing = []
    for pid, no, title in LESSONS:
        s, d = _wpq.call('/wp/v2/pages/%d?context=edit&_fields=content,link' % pid)
        assert s == 200, pid
        body, nq, na, anchor = extract(d['content']['raw'])
        if not body:
            missing.append(no)
            continue
        total_q += nq
        total_a += na
        # 只加定位索引，不提示答案、不给推导
        indexed = []
        for line in body.split('\n'):
            indexed.append(line)
            if line.startswith('### '):
                t = line[4:].strip()
                indexed.extend(['', '对应教材：L%02d' % no,
                                '原题小节：%s（教材原有标题）' % t, ''])
        body = '\n'.join(indexed)
        parts.extend(['---', '', '## 第%d课 %s' % (no, title), '',
                      '原题出处：%s' % (d['link'] + '#' + anchor if anchor else d['link']), '',
                      body, ''])
    parts.append('---\n')
    parts.append('合计 %d 课、%d 题，删除原有折叠答案 %d 处。' % (17 - len(missing), total_q, total_a))
    text = '\n'.join(parts) + '\n'
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('写入', OUT, len(text), '字', total_q, '题', total_a, '答案块', '缺课', missing)
    for bad in ('正确答案', '参考答案', '<details>', '答案：'):
        print(bad, text.count(bad))


if __name__ == '__main__':
    main()
