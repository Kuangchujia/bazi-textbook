# -*- coding: utf-8 -*-
"""r62 Q4-F：仅给首页「相关站点」段的外部链接补 rel="noopener noreferrer"。

约束（照 ChatGPT r62 裁定）：
- 只处理该段的外部链接（http/https），不改链接地址、不改锚文本。
- 不扩大到全站所有链接，不改内部链接。
- 在 post-build 阶段改生成的 HTML，不动 Markdown 源（避免污染 llms-full.txt）。
- 已有 rel 的保留其 baffle 值，仅确保含 noopener 与 noreferrer。
"""
import os
import re

SECTIONS = ['相关站点', '相關站點', 'Related sites', '関連サイト', '관련 사이트']


def _add_rel(html):
    # 只处理首页相关站点段：从该段标题的 id 锚点到下一个 <h2
    changed = 0
    for title in SECTIONS:
        # 直接匹配正文 h2（跳过左侧 TOC 里的同名链接）
        m = re.search(r'<h2[^>]*>\s*%s\s*</h2>' % re.escape(title), html)
        if not m:
            continue
        h2end = m.end()
        nxt = html.find('<h2', h2end)
        if nxt < 0:
            nxt = len(html)
        seg = html[h2end:nxt]
        new_seg, n = re.subn(
            r'<a\s+href="(https?://[^"]+)"([^>]*)>',
            lambda m: _fix_anchor(m.group(0), m.group(2)),
            seg,
        )
        if n:
            html = html[:h2end] + new_seg + html[nxt:]
            changed += n
        break
    return html, changed


def _fix_anchor(tag, attrs):
    m = re.search(r'rel="([^"]*)"', attrs)
    if m:
        vals = m.group(1).split()
        for v in ('noopener', 'noreferrer'):
            if v not in vals:
                vals.append(v)
        new_attrs = attrs.replace('rel="%s"' % m.group(1), 'rel="%s"' % ' '.join(vals))
    else:
        new_attrs = attrs + ' rel="noopener noreferrer"'
    return tag.replace(attrs, new_attrs, 1)


def _fix_hant_bazi_links(html):
    """r62 Q2：繁中教材页 62 条 /bazi/ 根相对链接改主站绝对地址 + rel。

    锚文本逐字不动、路径与主题不变、不新增/删除链接；仅改 href 与补 rel。
    """
    pat = re.compile(r'<a href="(/bazi/[^"]+)"((?:\s[^>]*)?)>')

    def repl(m):
        href, attrs = m.group(1), m.group(2)
        if 'rel=' in attrs:
            attrs = re.sub(r'rel="[^"]*"', 'rel="noopener noreferrer"', attrs)
        else:
            attrs = attrs + ' rel="noopener noreferrer"'
        return '<a href="https://jiayanyide.com%s"%s>' % (href, attrs)

    return pat.subn(repl, html)


def on_post_build(config):
    site_dir = config['site_dir']
    targets = ['index.html', 'en/index.html', 'zh-hant/index.html',
               'ja/index.html', 'ko/index.html']
    total = 0
    for rel in targets:
        fp = os.path.join(site_dir, rel.replace('/', os.sep))
        if not os.path.isfile(fp):
            continue
        h = open(fp, encoding='utf-8').read()
        out, n = _add_rel(h)
        if n:
            with open(fp, 'w', encoding='utf-8', newline='\n') as f:
                f.write(out)
            total += n
    print('[link_rel] related-sites external links fixed:', total)

    # Q2：繁中教材页 /bazi/ 死链
    q2 = 0
    tb = os.path.join(site_dir, 'zh-hant', 'textbook')
    if os.path.isdir(tb):
        for dp, dn, fs in os.walk(tb):
            for f in fs:
                if f != 'index.html':
                    continue
                fp = os.path.join(dp, f)
                h = open(fp, encoding='utf-8').read()
                out, n = _fix_hant_bazi_links(h)
                if n:
                    with open(fp, 'w', encoding='utf-8', newline='\n') as fo:
                        fo.write(out)
                    q2 += n
    print('[link_rel] zh-hant /bazi/ links fixed:', q2)
