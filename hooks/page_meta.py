"""逐页元数据注入（不改教材原文）。

十七课的 description／主站对应页／相关词条在构建期注入 page.meta，模板从
page.meta 读取；正文文件的字节只承载教材原文与编者导读，元数据不落盘到正文，
免得一改元数据就把正文哈希改动。

v1.0.0 的逐件 SHA256 基线存 SHA256SUMS-v1.0.0.txt（对应 Zenodo 归档版本）；
SHA256SUMS.txt 记录当前文件的哈希。

另在此生成三个机器可读文件：llms.txt（站点导读）、llms-full.txt（全书纯文本）、
index.json（结构化索引）。三者的标题与描述与本文件的 LESSONS／EXTRA 同源，
改描述只需改一处。
"""

import json
import os
import re
import subprocess

VERSION = "1.0.0"
PUBLISHED = "2026-11-26"          # v1.0.0 发布日；页面最后修订日另按 git 记录取值
DOI = "https://doi.org/10.5281/zenodo.24549949"

GLOSSARY = "https://jiayanyide.com/bazi/glossary/"
GLOSSARY_INDEX = "https://jiayanyide.com/bazi/glossary/terms/"
MAIN_LESSON = "https://jiayanyide.com/bazi/basic/lesson-%02d/"

# 词条：slug -> 显示名（主站词典实有页面）
TERMS = {
    "sizhu": "四柱",
    "rizhu": "日主",
    "yinyang": "阴阳",
    "wuxing": "五行",
    "tiangan": "天干",
    "dizhi": "地支",
    "canggan": "藏干",
    "shishen": "十神",
    "zhengguan": "正官",
    "qisha": "七杀",
    "zhengcai": "正财",
    "piancai": "偏财",
    "yongshen": "用神",
    "geju": "格局",
    "jishen": "吉神",
}

# 每课：description；主站课次；相关词条 slug
LESSONS = {
    "L01": ("八字由年、月、日、时四柱干支组成。本课介绍命与运的关系、周易与八字的源流、主要门派与典籍，并说明十七课的学习路线。",
            1, ["sizhu", "rizhu"]),
    "L02": ("阴阳学说、四象与五行学说是全书的地基。这一课讲五行的生克次序、四象的来路，以及「一体多面」为何要在不同维度下分别看。",
            2, ["yinyang", "wuxing"]),
    "L03": ("十天干的类象与属性、天干生克、天干与方位季节和人体部位的对应，以及天干五合的成合条件。理解天干，是读十神与格局的前一步。",
            3, ["tiangan"]),
    "L04": ("十二地支的五行与阴阳属性、与四季方位时辰的对应、四孟四正四库的分组、六十甲子的构成、地支藏干与地支生克。",
            4, ["dizhi", "canggan"]),
    "L05": ("本课讲六合、六冲、六害、三合局、会局与三刑的构成条件及作用差别，帮助理解地支组合及其对命局结构的影响。",
            5, ["dizhi"]),
    "L06": ("干支纪年如何起算、纪月为何以节气换月而不按农历初一、纪日与纪时的推算方法，附完整排盘示例与大运排法。这一课把年月日时推成四柱干支，为后续命局分析建立排盘基础。",
            6, ["sizhu", "rizhu", "canggan"]),
    "L07": ("长生十二宫的定义与十二个阶段，各阶段的力量对比，以及十天干在十二宫中的具体状态。用于衡量天干在某一地支上的实际力量。",
            7, []),
    "L08": ("日干如何确定、五行生克如何转化为十神，以及十神之间的生克关系。十神是八字分析的基本语言，先掌握排法，再学习类象。",
            8, ["shishen", "rizhu"]),
    "L09": ("正官、七杀、正偏财、印绶、食神的类象。同一个十神在不同位置、不同组合下含义会变，本课只讲基本象义，不急于下断语。",
            9, ["shishen", "zhengguan", "qisha", "zhengcai", "piancai"]),
    "L10": ("禄、刃、月劫的概念，通根与透干的分别，八字分析的基本次序，四吉神与四凶神的划分。这一课建立组合分析的框架。",
            10, ["shishen", "zhengguan"]),
    "L11": ("食神、财星、正官、印绶四吉神的类象与宜忌，讲清同一本体在不同组合下结论为何不同，是十神配合的第一组。",
            11, ["zhengguan", "zhengcai", "piancai", "jishen"]),
    "L12": ("伤官、禄、刃、七杀等凶神的类象与宜忌，并说明凶神逆用的思路，以及制化得当与否对组合分析的影响。",
            12, ["qisha", "shishen"]),
    "L13": ("十神在学业、事业、婚姻三个领域的具体取用：看哪些十神、在哪个位置看、怎样与岁运合看。属应用性质的练习课。",
            13, ["shishen"]),
    "L14": ("八字流派总览、自党与异党的划分、旺衰与强弱的区别、取用神的四大类型、得令得地得势的判据，以及用神忌神喜神仇神闲神的定义。",
            14, ["yongshen", "geju"]),
    "L15": ("旺衰判断的三大标准，身旺与身弱各自的判据与宜忌。旺衰不是给命局打分，而是决定取用方向。",
            15, ["yongshen"]),
    "L16": ("吉神、中性、凶神三类神煞，以及神煞运用的原则：以格局与旺衰为主，神煞为辅，不作单断依据。",
            16, ["jishen"]),
    "L17": ("原局、大运、流年三者的关系，大运吉凶的判断，流年与大运如何合看，附岁运的具体用法示例。全课的收束。",
            17, []),
}

# 一体多面的定义句。页面首屏、llms.txt、JSON-LD 的 DefinedTerm 三处逐字一致，
# 要改只改这一处，不要分别改三处文字。
YITI_DUOMIAN = ("一体多面，是指同一种太极之气因动静不同而分阴阳；"
                "放到具体命局中，其轻重与指向会随观察维度而改变。")

EXTRA = {
    "exercises/": "教材十七课原有练习题 63 道，按课次编排，不附标准答案或解题过程，并标注对应教材和原题小节，供读者自学复习。",
    "exercises/exercises/": "十七课练习手册全文：按课次照录各课「练习」小节题干，未改字、未另编题，每题标注对应教材课次与原题小节。",
    "contact/": "教材交流、内容勘误与课程咨询的联系渠道：邮箱与微信；另说明受理范围，不设购买与报名入口，不受理个案批命与排盘。",
    "method/": YITI_DUOMIAN + "附定维度、看力量、观组合三步次序与原文出处。",
    "notes/": "教材十七课中的邝楚嘉按语，按课次汇总，附导读与原文位置；点条目回到正文。",
}

TITLES = {
    "L01": "概论", "L02": "阴阳五行", "L03": "天干及五合", "L04": "地支",
    "L05": "地支关系", "L06": "八字排法", "L07": "长生十二宫", "L08": "十神排法",
    "L09": "十神类象", "L10": "十神组合（一）", "L11": "十神组合（二）",
    "L12": "十神组合（三）", "L13": "十神实战", "L14": "旺衰抑扶",
    "L15": "旺衰的用法", "L16": "神煞", "L17": "大运流年",
}

# 四篇的分界与篇名，取自各课第二行（第一篇 · 入门篇 …）。
PARTS = [
    ("第一篇 入门篇", 1, 5),
    ("第二篇 操作篇", 6, 7),
    ("第三篇 十神篇", 8, 12),
    ("第四篇 实战篇", 13, 17),
]


def _part_of(num):
    for name, lo, hi in PARTS:
        if lo <= num <= hi:
            return name
    return ""


def _build():
    desc, main, keys = {}, {}, {}
    for lid, (d, num, term_list) in LESSONS.items():
        url = "textbook/%s/" % lid
        desc[url] = d
        main[url] = {
            "num": num,
            "label": "第%d课" % num,
            "url": MAIN_LESSON % num,
            "terms": [{"name": TERMS[s], "url": "%s%s/" % (GLOSSARY, s)} for s in term_list],
            "index": GLOSSARY_INDEX,
        }
        keys[url] = [TERMS[s] for s in term_list]
    desc.update(EXTRA)
    return desc, main, keys


DESCRIPTIONS, MAIN_SITE, KEYWORDS = _build()


def _git_date(path):
    """取该文件最后一次提交的日期（YYYY-MM-DD）。取不到就回落发布日。"""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=5,
        )
        d = out.stdout.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return d
    except Exception:
        pass
    return PUBLISHED


def _word_count(text):
    """中文字数口径：汉字逐字计，连续拉丁字母／数字算一个词。"""
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9]+", text))
    return han + latin


_NOTE_ROW = re.compile(
    r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.+?)\s*\|\s*$")
_ANCHOR_NUM = re.compile(r"#an-(\d+)$")


def _notes_items(md, base):
    """从按语索引页的表格里取条目，供 JSON-LD 的 ItemList 使用。

    直接解析页面本身，索引改一条，机器可读那份同步改，不会两边对不上。
    """
    items = []
    for line in md.split("\n"):
        m = _NOTE_ROW.match(line.strip())
        if not m:
            continue
        section, href, title = m.group(1), m.group(2), m.group(3)
        # 页内写的是 textbook/L01.md#an-01，机读链接要的是部署后的目录地址。
        href = href.replace(".md#", "/#")
        url = base + href[3:] if href.startswith("../") else base + href.lstrip("/")
        a = _ANCHOR_NUM.search(href)
        lm = re.search(r"(L\d+)/?#an-", href)
        lid = lm.group(1) if lm else ""
        num = int(lid[1:]) if lid else 0
        items.append({
            "position": len(items) + 1,
            "name": title,
            "section": section,
            "url": url,
            "anchor": "an-%s" % a.group(1) if a else "",
            "lesson": lid,
            "lessonNo": num,
        })
    return items


def on_config(config):
    """把全书的章节清单与版本信息挂到 config.extra，模板与 JSON-LD 共用。"""
    base = config["site_url"]
    chapters = []
    for i in range(1, 18):
        lid = "L%02d" % i
        chapters.append({
            "num": i,
            "title": "第%d课 %s" % (i, TITLES[lid]),
            "url": "%stextbook/%s/" % (base, lid),
            "part": _part_of(i),
            "description": DESCRIPTIONS["textbook/%s/" % lid],
        })
    config["extra"]["chapters"] = chapters
    config["extra"]["book_version"] = VERSION
    config["extra"]["book_published"] = PUBLISHED
    config["extra"]["book_doi"] = DOI
    return config


def on_page_context(context, page, config, nav):
    url = page.url
    d = DESCRIPTIONS.get(url)
    if d and not page.meta.get("description"):
        page.meta["description"] = d
    if url in MAIN_SITE:
        page.meta["main_site"] = MAIN_SITE[url]
        page.meta["keywords"] = "、".join(KEYWORDS.get(url, []))
        num = MAIN_SITE[url]["num"]
        page.meta["lesson_no"] = num
        page.meta["section"] = _part_of(num)
    # 字数与修订日：JSON-LD 的 wordCount／dateModified 与页脚可见日期共用。
    page.meta["word_count"] = _word_count(page.markdown or "")
    page.meta["revised"] = _git_date(page.file.abs_src_path)
    if url == "notes/":
        page.meta["notes_items"] = _notes_items(page.markdown or "", config["site_url"])
    if url == "method/":
        page.meta["definition"] = YITI_DUOMIAN
    return context


# ── 机器可读文件 ────────────────────────────────────────────────────

def _md_to_text(md):
    """把教材 Markdown 折成可读纯文本，供 llms-full.txt 使用。"""
    lines = []
    for raw in md.split("\n"):
        s = raw.rstrip()
        if not s:
            lines.append("")
            continue
        if s.startswith("基础教材 ·"):          # 页眉行，不是内容
            continue
        if s.startswith("???"):                  # 折叠块标题保留为小标题
            m = re.search(r'"(.*?)"', s)
            if m:
                lines.append("【%s】" % m.group(1))
            continue
        s = re.sub(r"^>\s?", "", s)              # 引用符号
        s = re.sub(r"^#{1,6}\s*", "", s)         # 标题井号
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)   # 粗体
        s = re.sub(r"`([^`]*)`", r"\1", s)       # 行内代码
        s = re.sub(r"^\|[\s:\-|]+\|$", "", s)    # 表格分隔行
        if s.startswith("|") and s.endswith("|"):
            s = " ｜ ".join(x.strip() for x in s.strip("|").split("|"))
        s = re.sub(r"^\s*[-*]\s+", "· ", s)      # 列表
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def on_post_build(config):
    """生成 llms.txt、llms-full.txt 与 index.json。"""
    base = config["site_url"]
    site_dir = config["site_dir"]
    docs_dir = config["docs_dir"]

    # 一 · llms.txt：站点导读（llmstxt.org 的 H1 + 摘要 + 分节链接）
    L = []
    L.append("# 四柱八字基础教材")
    L.append("")
    L.append("> 邝楚嘉（嘉言一得）著，基础班四篇十七课、12+万字，2026 年 11 月发布 v1.0.0，"
             "DOI 10.5281/zenodo.24549949。教材原文、无答案练习与结构化附录在此免费公开阅读。")
    L.append("")
    L.append("本站是《四柱八字基础教材》的单一内容源。正文为作者自撰，逐课原文未删改。"
             "内容属传统命理理论，书中的判断与推演是该体系内部的结论，不宣称已获现代科学确证，"
             "也不构成吉凶占卜服务，亦不构成医学、法律或投资建议。引用请标注书名、作者、版本与 DOI。")
    L.append("")
    L.append("内容出自作者二十余年的排盘实践与十余年教学；引古籍原文处随文标注书名。")
    L.append("")
    L.append("## 正文（十七课）")
    L.append("")
    for i in range(1, 18):
        lid = "L%02d" % i
        url = "textbook/%s/" % lid
        L.append("- [第%d课 · %s](%s%s): %s" % (i, TITLES[lid], base, url, DESCRIPTIONS[url]))
    L.append("")
    L.append("## 练习")
    L.append("")
    L.append("- [练习说明](%sexercises/): %s" % (base, DESCRIPTIONS["exercises/"]))
    L.append("- [练习题手册（无答案）](%sexercises/exercises/): %s" % (base, DESCRIPTIONS["exercises/exercises/"]))
    L.append("")
    L.append("## 附录数据")
    L.append("")
    L.append("- [六十甲子表 CSV](%sappendix-data/bazi-jiazi.csv): 六十甲子与纳音的对照数据。" % base)
    L.append("- [十神查法 CSV](%sappendix-data/bazi-shishen.csv): 日干对十天干取十神的对照表。" % base)
    L.append("- [长生十二宫 CSV](%sappendix-data/bazi-changsheng.csv): 十天干在十二地支的长生状态。" % base)
    L.append("- [神煞查法 CSV](%sappendix-data/bazi-shensha.csv): 常用神煞的起法对照。" % base)
    L.append("")
    L.append("## 方法论")
    L.append("")
    L.append("- [一体多面](%smethod/): %s三步次序为定维度、看力量、观组合。" % (base, YITI_DUOMIAN))
    L.append("- [邝楚嘉按语索引](%snotes/): 十七课里作者的按语，按课次汇总，逐条回原文。" % base)
    L.append("")
    L.append("## 作者、版本与许可")
    L.append("")
    L.append("- [关于嘉言一得](%sauthor/): 作者简介、研究方向与公开档案。" % base)
    L.append("- [版权与版本说明](%srights/): 版本记录、DOI 与分层授权。" % base)
    L.append("- [课程与教学服务](%scourses/): 教材、练习与附录免费公开；研修班另行成书。" % base)
    L.append("- [联系与勘误](%scontact/): 教材交流、内容勘误与课程咨询的联系渠道；不设购买与报名入口。" % base)
    L.append("")
    L.append("授权分层，不统一：教材与练习为 CC BY-NC-SA 4.0，附录数据为 CC BY 4.0，自编脚本为 MIT。")
    L.append("")
    L.append("## 相关站点")
    L.append("")
    L.append("- [术数网 jiayanyide.com](https://jiayanyide.com/): 同一作者的术数主站，"
             "含十七课完整原文与例题、术语词典、专题研究。")
    L.append("- [中国历法与历史天文 kuangchujia.com](https://kuangchujia.com/): 节气与岁首、干支纪日、"
             "二十八宿宿度的考据与数据，与本站分属两套体系。")
    L.append("- [潮俗网 chaoshanwiki.com](https://chaoshanwiki.com/): 潮汕民俗数字知识库，"
             "与本站无内容交叠。")
    L.append("")
    L.append("## Optional")
    L.append("")
    L.append("- [全书纯文本 llms-full.txt](%sllms-full.txt): 十七课正文与练习的纯文本，供整本检索或语料使用。" % base)
    L.append("- [结构化索引 index.json](%sindex.json): 课次、篇名、描述、关键词与字数的机读清单。" % base)
    L.append("- [全站页面清单 sitemap.xml](%ssitemap.xml)" % base)
    L.append("- [源文件与版本记录](https://github.com/Kuangchujia/bazi-textbook)")
    L.append("")
    _write(os.path.join(site_dir, "llms.txt"), "\n".join(L))

    # 二 · llms-full.txt：全书纯文本
    SEP = "=" * 60
    F = []
    F.append("四柱八字基础教材（v%s，%s）" % (VERSION, PUBLISHED))
    F.append("作者：邝楚嘉（嘉言一得）　DOI：%s" % DOI)
    F.append("来源：%s" % base)
    F.append("授权：教材与练习 CC BY-NC-SA 4.0；附录数据 CC BY 4.0。引用请标注书名、作者、版本与 DOI。")
    F.append("说明：本文件为教材正文的纯文本汇编，供检索与语料使用；正式阅读请回到上述网址。")
    F.append("内容出自作者二十余年的排盘实践与十余年教学；引古籍原文处随文标注书名。")
    F.append("")
    for i in range(1, 18):
        lid = "L%02d" % i
        path = os.path.join(docs_dir, "textbook", "%s.md" % lid)
        with open(path, encoding="utf-8") as f:
            md = f.read()
        F.append(SEP)
        F.append("第%d课　%s（%s）" % (i, TITLES[lid], _part_of(i)))
        F.append("网址：%stextbook/%s/" % (base, lid))
        F.append(SEP)
        F.append("")
        F.append(_md_to_text(md))
        F.append("")
    for name, title in (("exercises/exercises.md", "练习题手册（无答案）"),):
        path = os.path.join(docs_dir, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                F.append(SEP)
                F.append(title)
                F.append("网址：%sexercises/exercises/" % base)
                F.append(SEP)
                F.append("")
                F.append(_md_to_text(f.read()))
                F.append("")
    _write(os.path.join(site_dir, "llms-full.txt"), "\n".join(F))

    # 三 · index.json：结构化索引
    pages = []
    for i in range(1, 18):
        lid = "L%02d" % i
        url = "textbook/%s/" % lid
        path = os.path.join(docs_dir, "textbook", "%s.md" % lid)
        with open(path, encoding="utf-8") as f:
            words = _word_count(f.read())
        pages.append({
            "url": base + url,
            "type": "lesson",
            "lesson": i,
            "part": _part_of(i),
            "title": "第%d课 %s" % (i, TITLES[lid]),
            "description": DESCRIPTIONS[url],
            "keywords": KEYWORDS.get(url, []),
            "mainSite": MAIN_LESSON % i,
            "words": words,
        })
    pages.insert(0, {
        "url": base,
        "type": "home",
        "title": "四柱八字基础教材",
        "description": DESCRIPTIONS.get("", "四篇十七课、12+万字的四柱八字基础教材，含无答案练习与结构化附录。"),
    })
    for url, kind, title in (
        ("exercises/", "exercises", "练习说明"),
        ("exercises/exercises/", "exercises", "练习题手册（无答案）"),
        ("author/", "about", "关于嘉言一得"),
        ("rights/", "about", "版权与版本说明"),
        ("courses/", "about", "课程与教学服务"),
        ("method/", "method", "一体多面方法论"),
        ("notes/", "method", "邝楚嘉按语索引"),
        ("contact/", "about", "联系与勘误"),
    ):
        pages.append({
            "url": base + url,
            "type": kind,
            "title": title,
            "description": DESCRIPTIONS.get(url, ""),
        })
    index = {
        "site": base,
        "name": "四柱八字基础教材",
        "version": VERSION,
        "published": PUBLISHED,
        "author": {"name": "邝楚嘉", "alternateName": "嘉言一得"},
        "license": "CC BY-NC-SA 4.0（教材与练习）；CC BY 4.0（附录数据）",
        "doi": DOI,
        "chapters": config["extra"]["chapters"],
        "pages": pages,
    }
    _write(os.path.join(site_dir, "index.json"),
           json.dumps(index, ensure_ascii=False, indent=2))
