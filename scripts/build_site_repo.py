# -*- coding: utf-8 -*-
"""P0-2/3/4/7/8：建立单一内容源仓库骨架并做原文一致性核验。"""
import os, csv, shutil, hashlib, subprocess
from bs4 import BeautifulSoup
import _wpq

SRC = r'D:\OneDrive\文档\Obsidian Vault\术数网\code\八字栏目\open_bazi_repo'
FROZEN = os.path.join(SRC, '_frozen_20261126')
DST = r'D:\OneDrive\文档\Obsidian Vault\术数网\code\八字栏目\site_repo'

LESSONS = [(227, 1, '概论'), (228, 2, '阴阳五行'), (229, 3, '天干及五合'),
           (230, 4, '地支'), (232, 5, '地支关系'), (233, 6, '八字排法'),
           (234, 7, '长生十二宫'), (235, 8, '十神排法'), (236, 9, '十神类象'),
           (237, 10, '十神组合（一）'), (238, 11, '十神组合（二）'),
           (239, 12, '十神组合（三）'), (240, 13, '十神实战'),
           (241, 14, '旺衰抑扶的基本概念'), (242, 15, '旺衰的用法'),
           (243, 16, '神煞'), (244, 17, '大运流年的看法')]


def raw_of(pid):
    s, d = _wpq.call('/wp/v2/pages/%d?context=edit&_fields=content' % pid)
    assert s == 200, pid
    return d['content']['raw']


def cells(tr):
    return [c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'])]


def write_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print('  csv', os.path.basename(path), len(rows), 'rows')


def build_csv(appendix):
    # 1 六十甲子（第 4 课）
    soup = BeautifulSoup(raw_of(230), 'html.parser')
    rows = []
    for tr in soup.find('table').find_all('tr')[1:]:
        cs = cells(tr)
        for i in range(0, len(cs) - 1, 2):
            if cs[i].isdigit() and cs[i + 1]:
                rows.append([int(cs[i]), cs[i + 1], 'L04', '第4课·六十甲子表'])
    rows.sort()
    write_csv(os.path.join(appendix, 'bazi-jiazi.csv'),
              ['id', 'name', 'source_lesson_id', 'source_reference'], rows)

    # 2 十神查法（第 9 课，关系/命名/象义表）
    soup = BeautifulSoup(raw_of(236), 'html.parser')
    rows = []
    for t in soup.find_all('table'):
        trs = t.find_all('tr')
        if not trs:
            continue
        head = cells(trs[0])
        if len(head) >= 3 and head[0] == '关系' and head[1] == '命名':
            for i, tr in enumerate(trs[1:], 1):
                c = cells(tr)
                if len(c) >= 3:
                    rows.append([i, c[0], c[1], c[2], 'L09', '第9课·十神关系表'])
    write_csv(os.path.join(appendix, 'bazi-shishen.csv'),
              ['id', 'relation', 'name', 'meaning', 'source_lesson_id', 'source_reference'], rows)

    # 3 长生十二宫（第 7 课第三张表：天干＋十二宫）
    soup = BeautifulSoup(raw_of(234), 'html.parser')
    tables = soup.find_all('table')
    t = tables[2]
    head = cells(t.find_all('tr')[0])
    rows = []
    for i, tr in enumerate(t.find_all('tr')[1:], 1):
        c = cells(tr)
        if len(c) == len(head):
            rows.append([i, c[0]] + c[1:] + ['L07', '第7课·十天干在十二宫中的状态'])
    write_csv(os.path.join(appendix, 'bazi-changsheng.csv'),
              ['id', 'name'] + head[1:] + ['source_lesson_id', 'source_reference'], rows)

    # 4 神煞查法（第 16 课，项目/内容表：只收名称与教材原文规则）
    soup = BeautifulSoup(raw_of(243), 'html.parser')
    seen, rows = set(), []
    for t in soup.find_all('table'):
        trs = t.find_all('tr')
        if not trs or cells(trs[0])[:2] != ['项目', '内容']:
            continue
        for tr in trs[1:]:
            c = cells(tr)
            if len(c) >= 2 and c[0] and c[1] and (c[0], c[1]) not in seen:
                seen.add((c[0], c[1]))
                rows.append([len(rows) + 1, c[0], c[1], 'L16', '第16课·神煞表'])
    write_csv(os.path.join(appendix, 'bazi-shensha.csv'),
              ['id', 'name', 'rule_text', 'source_lesson_id', 'source_reference'], rows)


def main():
    for p in ['docs/textbook', 'docs/errata', 'docs/exercises', 'docs/appendix-data',
              'scripts', '.github/workflows']:
        os.makedirs(os.path.join(DST, p), exist_ok=True)

    # 教材正文：逐字节复制并比对冻结件；冻结件保持原样，不回写。
    # 少数课文与冻结件存在既定差异，按白名单放行：差异仅限「优化者」一行，
    # 其它任何字节变动仍然报警。
    APPROVED_SIGN_EDITS = {3: '邝楚嘉（嘉言一得）', 4: '邝楚嘉（嘉言一得）',
                           9: '邝楚嘉（嘉言一得）', 10: '邝楚嘉（嘉言一得）'}
    sums = []
    for pid, no, title in LESSONS:
        src = os.path.join(SRC, 'lessons', 'lesson-%02d.md' % no)
        dst = os.path.join(DST, 'docs', 'textbook', 'L%02d.md' % no)
        frozen = os.path.join(FROZEN, 'lessons', 'lesson-%02d.md' % no)
        b = open(src, 'rb').read()
        fb = open(frozen, 'rb').read()
        if b != fb:
            assert no in APPROVED_SIGN_EDITS, '原文与冻结件不一致 L%02d' % no
            sign = APPROVED_SIGN_EDITS[no]
            import re as _re
            norm = lambda t: _re.sub(r'优化者 ：.*?(?= 优化说明|\r?\n|$)', '优化者 ：<SIGN>',
                                     t.decode('utf-8'))
            assert norm(b) == norm(fb), 'L%02d 白名单外仍有改动，停止' % no
            assert sign in b.decode('utf-8'), 'L%02d 未见既定差异行' % no
        open(dst, 'wb').write(b)
        assert open(dst, 'rb').read() == b
        sums.append((hashlib.sha256(b).hexdigest(), 'docs/textbook/L%02d.md' % no, len(b)))
        print('L%02d byte-identical %d bytes' % (no, len(b)))
    with open(os.path.join(DST, 'SHA256SUMS.txt'), 'w', encoding='utf-8', newline='\n') as f:
        for h, rel, n in sums:
            f.write('%s  %s (%d bytes)\n' % (h, rel, n))

    # 练习手册
    shutil.copy2(os.path.join(SRC, '练习题手册·无答案.md'),
                 os.path.join(DST, 'docs', 'exercises', 'exercises.md'))
    with open(os.path.join(DST, 'docs', 'exercises', 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 练习题手册（无答案）\n\n'
                '本目录收《四柱八字基础教材》十七课练习题 63 道，照录教材原题，'
                '不提供标准答案、参考答案及解题过程。\n\n'
                '每题下的「对应教材」「原题小节」只用于定位学习内容，不构成答案提示。\n')

    # 附录数据
    build_csv(os.path.join(DST, 'docs', 'appendix-data'))

    # 校勘目录占位
    with open(os.path.join(DST, 'docs', 'errata', '.gitkeep'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('校勘另册待编者指定条目；不得以占位文件虚构校勘内容。\n')

    # 文档站首页
    with open(os.path.join(DST, 'docs', 'index.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 四柱八字基础教材\n\n'
                '邝楚嘉（嘉言一得）四篇十七课，约十二万字。此处是教材原文的单一内容源与在线阅读站。\n\n'
                '- [教材正文 L01—L17](textbook/L01.md)\n'
                '- [练习题手册（无答案）](exercises/README.md)\n'
                '- [校勘另册](errata/.gitkeep)\n'
                '- [结构化附录](appendix-data/)\n\n'
                '本站只提供学术讨论，不涉及具体吉凶占卜。教材原文未删改；校勘与附录为独立层级。\n')

    # MkDocs 配置
    nav = '\n'.join('      - 第%d课: textbook/L%02d.md' % (n, n) for _, n, _ in LESSONS)
    mk = ('site_name: 四柱八字基础教材\n'
          'site_url: https://bazi-textbook.jiayanyide.com/\n'
          'docs_dir: docs\n'
          'theme:\n  name: material\n  language: zh-CN\n'
          'nav:\n  - 首页: index.md\n  - 教材正文:\n' + nav + '\n'
          '  - 练习:\n    - 说明: exercises/README.md\n    - 题目: exercises/exercises.md\n'
          '  - 附录数据:\n    - 六十甲子: appendix-data/bazi-jiazi.csv\n'
          '    - 十神查法: appendix-data/bazi-shishen.csv\n'
          '    - 长生十二宫: appendix-data/bazi-changsheng.csv\n'
          '    - 神煞查法: appendix-data/bazi-shensha.csv\n')
    open(os.path.join(DST, 'mkdocs.yml'), 'w', encoding='utf-8', newline='\n').write(mk)

    # CI：仅构建文档，不做 PDF/EPUB
    yml = ('name: docs\n'
           'on:\n  push:\n    branches: [main]\n'
           'jobs:\n  build:\n    runs-on: ubuntu-latest\n'
           '    steps:\n      - uses: actions/checkout@v4\n'
           '      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.12"\n'
           '      - run: pip install mkdocs-material\n      - run: mkdocs build --strict\n')
    open(os.path.join(DST, '.github', 'workflows', 'docs.yml'), 'w', encoding='utf-8', newline='\n').write(yml)

    # 权利状态：当前不授权
    rights = ('# 权利状态\n\n'
              '本仓库公开用于教材阅读、内容核验及项目版本记录。'
              '除适用法律规定的权利和 GitHub 平台服务条款所允许的必要操作外，'
              '本仓库暂未授予第三方复制、改编、再发布及商业使用许可。'
              '各类内容的最终授权范围与许可协议将在权利确认后另行公布。\n\n'
              '目标分层（尚未生效）：教材正文、练习、校勘 CC BY-NC-SA 4.0；'
              '附录数据 CC BY 4.0；自编脚本 MIT。\n')
    open(os.path.join(DST, 'RIGHTS.md'), 'w', encoding='utf-8', newline='\n').write(rights)

    readme = ('# 四柱八字基础教材 · 开放文本库\n\n'
              '十七课教材原文、63 题无答案练习、校勘另册与结构化附录。'
              '在线阅读地址：https://bazi-textbook.jiayanyide.com/（待配置）。\n\n'
              '当前权利状态见 [RIGHTS.md](RIGHTS.md)。原文冻结与校验见 '
              '[SHA256SUMS.txt](SHA256SUMS.txt)。\n')
    open(os.path.join(DST, 'README.md'), 'w', encoding='utf-8', newline='\n').write(readme)
    open(os.path.join(DST, '.gitignore'), 'w', encoding='utf-8', newline='\n').write('site/\n__pycache__/\n*.pyc\n')

    for fn in ['export_lessons_markdown.py', 'build_question_book.py',
               'freeze_p0.py', 'build_site_repo.py']:
        p = os.path.join(os.path.dirname(__file__), fn)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(DST, 'scripts', fn))

    print('site repo built at', DST)

    # 本地 Git 初始化与首次提交
    subprocess.run(['git', 'init', '-q'], cwd=DST, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=DST, check=True)
    r = subprocess.run(['git', '-c', 'user.name=wb-build', '-c', 'user.email=wb@local',
                        'commit', '-q', '-m', 'P0: 教材原文单一内容源首次固化'],
                       cwd=DST, capture_output=True, text=True)
    print('git commit rc', r.returncode, (r.stdout + r.stderr)[:200])
    r2 = subprocess.run(['git', 'log', '-1', '--format=%H %s'], cwd=DST,
                        capture_output=True, text=True)
    print('HEAD', r2.stdout.strip())


if __name__ == '__main__':
    main()
