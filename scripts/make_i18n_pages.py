# -*- coding: utf-8 -*-
"""把主站已发布的四语教材正文转成 MkDocs 后缀页（不改简中原文、不改既有 URL）。

输入：_i18n_work/raw/lessons.json（主站 REST 抓取的 17 课 × 4 语 rendered）
输出：docs/textbook/Lxx.<lang>.md

处理边界：
- 只取 .jy-wrap 内的正文节点；剥掉语言切换行、WP 专属 jy-toc 目录、编辑器残留。
- 折叠块 <details> 转成 MkDocs pymdownx.details 的 ??? 语法，答案保留。
- 主站内链改指本站同语路径；术语链保留主站绝对地址（本站无对应页）。
- 页头写统一语言切换条，指向本站五语同名页。
"""
import json, os, re, sys, html
from bs4 import BeautifulSoup, Tag, NavigableString

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_i18n_work', 'raw', 'lessons.json')
DST = os.path.join(ROOT, 'docs', 'textbook')

SITE = 'https://bazi-textbook.jiayanyide.com/'
MAIN = 'https://jiayanyide.com'
LANGS = ['zh', 'zh-hant', 'en', 'ja', 'ko']
NAME = {'zh': '简体中文', 'zh-hant': '繁體中文', 'en': 'English', 'ja': '日本語', 'ko': '한국어'}
# 主站路径段 → 本站路径段
SEG = {'zh': '', 'zh-hant': 'zh-hant/', 'en': 'en/', 'ja': 'ja/', 'ko': 'ko/'}

# 课次标题：从简中原文取，四语页的 H1 用各自译文（保留主站已验收文字）。
ZH_TITLE = {}
for i in range(1, 18):
    p = os.path.join(DST, 'L%02d.md' % i)
    with open(p, encoding='utf-8') as f:
        m = re.search(r'^#\s+(.+)$', f.read(), re.M)
    ZH_TITLE['%02d' % i] = m.group(1).strip() if m else '第%d课' % i


def esc_inline(s):
    """正文里出现的裸尖括号转义，避免被当 HTML 标签。"""
    return re.sub(r'<(?!/?(?:a|em|strong|code|br|sup|sub)\b)[^>]*>', lambda m: html.escape(m.group(0)), s)


def conv_inline(node):
    if isinstance(node, NavigableString):
        s = str(node)
        s = re.sub(r'\s+', ' ', s)
        if not s.strip():
            return ' ' if s else ''
        return esc_inline(s)
    if not isinstance(node, Tag):
        return ''
    name = node.name
    inner = ''.join(conv_inline(c) for c in node.children)
    inner = re.sub(r' {2,}', ' ', inner).strip()
    if name == 'a':
        href = node.get('href', '')
        txt = inner or href
        href = rewrite_link(href, cur_lang)
        return '[%s](%s)' % (txt, href)
    if name in ('strong', 'b'):
        return '**%s**' % inner if inner else ''
    if name in ('em', 'i'):
        return '*%s*' % inner if inner else ''
    if name == 'code':
        return '`%s`' % inner if inner else ''
    if name == 'br':
        return '<br>'
    if name == 'img':
        return ''
    return inner


def rewrite_link(href, lang):
    if not href:
        return href
    href = html.unescape(href)
    # 主站本课/邻课 → 本站同语同名课
    m = re.match(r'^https?://jiayanyide\.com/bazi/(?:zh-hant|en|ja|ko)?/?basic/lesson-(\d\d)/?$', href)
    if m:
        # 后缀页与 Lxx.<lang>.md 同目录；插件按当前语言解析同名后缀页。
        return 'L%s.md' % m.group(1)
    # 主站本站首页 → 教材站对应语首页
    if re.match(r'^https?://jiayanyide\.com/bazi/(?:zh-hant|en|ja|ko)?/?$', href):
        return SITE + SEG[lang]
    # 教材子域自身绝对地址 → 相对
    m = re.match(r'^https?://bazi-textbook\.jiayanyide\.com/(.*)$', href)
    if m:
        return m.group(1)
    return href


def render_table(node):
    rows = []
    for tr in node.find_all('tr'):
        cells = []
        for c in tr.find_all(['th', 'td']):
            t = ''.join(conv_inline(x) for x in c.children).strip().replace('|', '\\|')
            cells.append(t)
        if cells:
            rows.append(cells)
    if not rows:
        return ''
    out = ['| ' + ' | '.join(rows[0]) + ' |',
           '| ' + ' | '.join(['---'] * len(rows[0])) + ' |']
    for r in rows[1:]:
        r = r + [''] * (len(rows[0]) - len(r))
        out.append('| ' + ' | '.join(r[:len(rows[0])]) + ' |')
    return '\n'.join(out)


def render_details(node, depth=0):
    s = node.find('summary')
    title = ''.join(conv_inline(x) for x in s.children).strip() if s else '详情'
    # 折叠答案统一用 ???+ 展开块（MkDocs admonition/details）
    out = ['???+ "%s"' % title.replace('"', '&quot;')]
    for c in node.children:
        if c is s or not isinstance(c, Tag):
            continue
        # 折叠块内常有 ol/ul 里再套 li>ol 的情况；render_block 已按递归取全部 li。
        chunk = render_block(c, depth + 1)
        if chunk:
            out += ['    ' + line if line else '' for line in chunk.split('\n')]
    return '\n'.join(out)


def render_block(node, depth=0):
    name = node.name
    if name == 'table':
        return render_table(node)
    if name == 'details':
        return render_details(node, depth)
    if name in ('h1', 'h2', 'h3', 'h4'):
        t = ''.join(conv_inline(x) for x in node.children).strip()
        return ('#' * int(name[1])) + ' ' + t if t else ''
    if name == 'p':
        t = ''.join(conv_inline(x) for x in node.children).strip()
        if not t:
            return ''
        return t
    if name == 'div':
        # 有的语种把整节裹在 div.jy-block 里，必须递归渲染内部块，不能只取内联文字。
        parts = []
        for c in node.children:
            if isinstance(c, Tag):
                r = render_block(c, depth)
                if r:
                    parts.append(r)
            elif isinstance(c, NavigableString):
                t = conv_inline(c).strip()
                if t:
                    parts.append(t)
        return '\n\n'.join(parts)
    if name in ('ul', 'ol'):
        out = []
        for i, li in enumerate(node.find_all('li', recursive=False), 1):
            t = ''.join(conv_inline(x) for x in li.children).strip()
            pre = ('%d. ' % i) if name == 'ol' else '- '
            out.append(pre + t)
        return '\n'.join(out)
    if name == 'blockquote':
        lines = [render_block(x, depth) for x in node.find_all(['p', 'ul', 'ol'], recursive=False)]
        return '\n'.join('> ' + l for l in '\n'.join(x for x in lines if x).split('\n'))
    if name == 'hr':
        return '---'
    if name == 'pre':
        return '```\n%s\n```' % node.get_text().rstrip()
    # 容器：递归子节点
    parts = []
    for c in node.children:
        if isinstance(c, Tag):
            r = render_block(c, depth)
            if r:
                parts.append(r)
    return '\n\n'.join(parts)


def switch_bar(lang, num):
    """语言条用站点根相对路径；构建后各语前缀由 i18n 插件补出。"""
    items = []
    for L in LANGS:
        href = '/%stextbook/L%02d/' % (SEG[L], num)
        items.append(('**%s**' % NAME[L]) if L == lang else '[%s](%s)' % (NAME[L], href))
    return ' ｜ '.join(items)


def build_one(lang, num):
    global cur_lang
    cur_lang = lang
    d = json.load(open(SRC, encoding='utf-8'))
    x = d['%s_%02d' % (lang, num)]
    soup = BeautifulSoup(x['content'], 'html.parser')
    wrap = soup.select_one('.jy-wrap') or soup
    blocks = []
    for node in wrap.children:
        if not isinstance(node, Tag):
            continue
        cls = ' '.join(node.get('class', []))
        txt = node.get_text(' ', strip=True)
        if node.name in ('style', 'script', 'nav'):
            continue
        if 'jy-eyebrow' in cls or 'jy-psub' in cls or 'jy-switch' in cls:
            continue
        if node.name == 'p' and ('简体中文' in txt or '簡體中文' in txt or '한국어 원문' in txt or '中文原文' in txt):
            if len(txt) < 40:
                continue
        if node.name == 'h1':
            continue  # 用本地 H1，语言标题从译文取
        r = render_block(node)
        if r:
            blocks.append(r)
    # 取译文 H1
    h1 = ''
    for node in wrap.children:
        if isinstance(node, Tag) and node.name == 'h1':
            h1 = node.get_text(' ', strip=True)
            break
    h1 = h1 or ZH_TITLE['%02d' % num]
    # 描述：主站 excerpt 去标签，兜底用简中
    ex = BeautifulSoup(x['excerpt'], 'html.parser').get_text(' ', strip=True)
    ex = re.sub(r'\s+', ' ', ex).strip()[:160]
    if not ex:
        ex = ZH_TITLE['%02d' % num]
    body = [
        '---',
        'lang: %s' % lang,
        'source_url: %s' % x['link'],
        'description: %s' % json.dumps(ex, ensure_ascii=False),
        '---',
        '',
        '# %s' % h1,
        '',
        switch_bar(lang, num),
        '',
    ]
    body.append('\n\n'.join(blocks))
    out = os.path.join(DST, 'L%02d.%s.md' % (num, lang))
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(body).rstrip() + '\n')
    return out, len('\n'.join(body))


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if arg == 'all':
        jobs = [(l, n) for l in ['en', 'ja', 'ko', 'zh-hant'] for n in range(1, 18)]
    else:
        jobs = [(arg, int(sys.argv[2]))]
    for l, n in jobs:
        p, size = build_one(l, n)
        print(os.path.basename(p), size)
    print('done', len(jobs))
