# 四柱八字基础教材 · 开放文本库

十七课教材原文、63 题无答案练习、结构化附录与构建脚本。在线阅读地址：https://bazi-textbook.jiayanyide.com/

授权状态：教材与练习 CC BY-NC-SA 4.0，附录数据 CC BY 4.0，自编脚本 MIT（2026-11-26 生效）。详见 [RIGHTS.md](RIGHTS.md)。v1.0.0 冻结基线的逐件 SHA256 见 [SHA256SUMS-v1.0.0.txt](SHA256SUMS-v1.0.0.txt)，当前文件哈希见 [SHA256SUMS.txt](SHA256SUMS.txt)。

归档 DOI：[10.5281/zenodo.24549949](https://doi.org/10.5281/zenodo.24549949)

## English

**Four Pillars of Destiny: Foundational Textbook** — open, citable edition, version 1.0.0.

A 17-lesson introductory textbook on the Four Pillars (Bazi) system, written in Chinese and published as a structured open repository: the complete lesson text, 63 practice questions without answers, four machine-readable CSV appendices, and the build scripts.

- Read online: https://bazi-textbook.jiayanyide.com/
- Archived version: https://doi.org/10.5281/zenodo.24549949
- Cite as: Kuang, C. (2026). 四柱八字基础教材 (Version 1.0.0). Zenodo. https://doi.org/10.5281/zenodo.24549949

**Scope.** The course runs from the sexagenary cycle, yin-yang and the five phases, the ten heavenly stems and twelve earthly branches, through the ten gods (shishen), patterns (geju), strength assessment, spirits and shensha, to luck cycles. It is a teaching text within the traditional Chinese metaphysics tradition: its judgments are internal to that system and are not presented as scientifically established.

**Editorial stance.** The lesson text is unaltered from the 2024 course handouts. Where schools disagree, the divergence is left standing rather than harmonised; doubtful points are marked as doubtful. The repository stores the primary text only — no answers, no case readings, no interpretive additions.

**Structure.**

| Path | Content |
|---|---|
| `docs/textbook/` | Lesson text, L01–L17 |
| `docs/exercises/` | 63 practice questions, no answers |
| `docs/appendix-data/` | Four CSV tables; every row carries `source_lesson_id` and `source_reference` |
| `scripts/` | Build and export scripts |

**Licensing is layered, not uniform.** Textbook and exercises: CC BY-NC-SA 4.0. Appendix data: CC BY 4.0. Scripts: MIT. Commercial use of the textbook requires separate permission. There is no repository-wide single LICENSE; the per-directory split in [RIGHTS.md](RIGHTS.md) governs.

**On the character count.** Chinese materials here state 「12+万字」 — over 120,000 characters. The exact figure depends on whether punctuation and inline markup are counted, so a threshold is given rather than a precise number.
