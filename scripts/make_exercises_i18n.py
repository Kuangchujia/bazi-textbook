# -*- coding: utf-8 -*-
"""从四语教材正文抽取「练习」段，生成各语练习手册后缀页。

不重译：题目与折叠答案都取自主站已发布、已验收的四语正文。
边界：练习段 = 二级标题「练习/練習/연습/Practice」起，到「下节预告/次課予告/다음 과 예고/Next lesson」止。
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'docs', 'exercises')
START = {'zh-hant': '練習', 'en': 'Practice', 'ja': '練習', 'ko': '연습'}
STOP = {'zh-hant': '下節預告', 'en': 'Next lesson', 'ja': '次課予告', 'ko': '다음 과 예고'}
INTRO = {
    'zh-hant': '本手冊按課次照錄《四柱八字基礎教材》十七課公開頁面的練習題與原摺疊答案，未改字、未另編題。',
    'en': 'This booklet reproduces the practice questions and the original folded answers from the '
          'seventeen published lessons of the foundation course, lesson by lesson, without rewriting '
          'or adding questions.',
    'ja': 'この手帳は『四柱八字基礎教材』十七課の公開ページにある練習問題と元の折りたたみ解答を、'
          '課ごとに照録したものです。字句は改めず、問題を新たに作っていません。',
    'ko': '이 책자는 『사주팔자 기초 교재』 열일곱 과의 공개 페이지에 있는 연습 문제와 원래 접힌 답을 '
          '과별로 그대로 옮긴 것입니다. 글자를 고치거나 새 문제를 만들지 않았습니다.',
}
BAR = {
    'zh-hant': '简体中文', 'en': '简体中文', 'ja': '简体中文', 'ko': '简体中文',
}


def extract(lang, num):
    p = os.path.join(ROOT, 'docs', 'textbook', 'L%02d.%s.md' % (num, lang))
    s = open(p, encoding='utf-8').read()
    heads = [(m.start(), m.group(0)[3:].strip()) for m in re.finditer(r'^## .*$', s, re.M)]
    a = next((p0 for p0, t in heads if t == START[lang]), None)
    if a is None:
        return ''
    b = next((p0 for p0, t in heads if p0 > a and t.startswith(STOP[lang])), len(s))
    return s[a:b].strip()


def build(lang):
    DESC = {
        'zh-hant': '十七課練習題與原摺疊答案',
        'en': 'Practice questions and original folded answers for all seventeen lessons',
        'ja': '十七課の練習問題と元の折りたたみ解答',
        'ko': '열일곱 과의 연습 문제와 원래 접힌 답',
    }
    parts = ['---', 'lang: %s' % lang, 'description: %s' % DESC[lang], '---', '', '# %s' % {
        'zh-hant': '四柱八字基礎教材十七課 · 練習題手冊（含原摺疊答案）',
        'en': 'Foundation Course, Seventeen Lessons · Practice Booklet (with original folded answers)',
        'ja': '四柱八字基礎教材十七課 · 練習問題手帳（元の折りたたみ解答つき）',
        'ko': '사주팔자 기초 교재 열일곱 과 · 연습 문제 책자 (원래 접힌 답 포함)',
    }[lang], '', INTRO[lang], '', '---', '']
    count = 0
    for n in range(1, 18):
        seg = extract(lang, n)
        if not seg:
            continue
        # 去掉段首二级标题，用课次作二级标题
        seg = re.sub(r'^## .*\n', '', seg, count=1).strip()
        parts += ['## %s %02d' % ({'zh-hant': '第', 'en': 'Lesson', 'ja': '第', 'ko': '제'}[lang], n)
                  if lang != 'en' else '## Lesson %02d' % n, '', seg, '']
        count += len(re.findall(r'^### ', seg, re.M))
    out = os.path.join(DST, 'exercises.%s.md' % lang)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(parts).rstrip() + '\n')
    print(lang, 'questions', count, 'chars', sum(len(x) for x in parts))


if __name__ == '__main__':
    for lang in ['zh-hant', 'en', 'ja', 'ko']:
        build(lang)
