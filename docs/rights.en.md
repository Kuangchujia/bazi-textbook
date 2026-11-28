---
lang: en
description: "The version record, DOI and tiered licensing of the Foundation Textbook of the Four Pillars and Eight Characters: textbook and exercises CC BY-NC-SA 4.0, appendix data CC BY 4.0, self-written scripts MIT."
---

# Rights and Version Notes

## Version

| Item | Content |
|---|---|
| Formal title | Foundation Textbook of the Four Pillars and Eight Characters |
| Author | Jiayanyide (Kuang Chujia) |
| Version | v1.0.0 |
| Release date | 2026-11-26 |
| DOI | [10.5281/zenodo.24549949](https://doi.org/10.5281/zenodo.24549949) |
| Archive record | [zenodo.org/records/24549949](https://zenodo.org/records/24549949) |
| Source files and version record | [github.com/Kuangchujia/bazi-textbook](https://github.com/Kuangchujia/bazi-textbook) |

The version content is governed by the Zenodo archive package; the repository tag `v1.0.0` corresponds to the commit at the time of archiving. Later changes to the repository description and pages do not constitute a new version of the textbook text.

| Version | Date | Notes |
|---|---|---|
| v1.0.0 | 2026-11-26 | First public release, archived at Zenodo, DOI 10.5281/zenodo.24549949 |

### Editor's introduction and file checksums

Before the main text of each lesson there is an "editor's introduction", explaining what the lesson covers and in what order; it is added by the editor and is not part of the original textbook. Before some notes there are invisible empty anchors (`#an-01` and the like), so that the index of notes can jump straight to the passage; they produce no visible text. The introductions and the page metadata (descriptions, links to related entries) are not counted as main text and do not change the licences at any tier.

The per-file SHA256 baseline at the v1.0.0 archive is kept in the repository as `SHA256SUMS-v1.0.0.txt`; `SHA256SUMS.txt` records the hashes of the current files. If the two differ, that file has been changed since archiving.

### Layers of content: who said which sentence

The words on the pages fall into four layers with different ownership; they should not be confused when citing:

| Layer | Marker on the page | Ownership |
|---|---|---|
| The judgements and system of the textbook (the bulk of the book) | Discussions, rules, formulas and choices in the main text where no book title is marked | The author's summary of more than twenty years of predictive practice and more than ten years of teaching |
| Original textbook text | Below "complete textbook text"; footer note "original text, unaltered" | Written by the author, v1.0.0 archive |
| Editor's introduction | "**Editor's introduction** (not the original textbook text)" at the head of a lesson | Added by the editor to set out the scope and order of the lesson |
| Supplementary reading | Folded blocks "Further reading: …" and "Appendix: …" | Extended material in the original textbook, archived together with the main text |
| Quotations from classics and schools | "Classical source", "the *Yuanhai Ziping* says", "the *Sanming Tonghui* …" | The original authors; the textbook only excerpts them; book titles are given in each lesson |

The skeleton of the textbook is the author's own basic teaching system, not a colloquial rewriting of an ancient classic, nor a record of a school's lineage. Classical texts occupy a place of supplement, comparison and further reading, with titles marked in the text so readers can check the originals; passages without a book title are judgements and teaching positions the author has induced from practice, conclusions internal to that system, not claimed to have been confirmed by modern science.

When citing the textbook, please identify the layer cited according to the table above: do not treat an editor's introduction or a classical quotation as the original textbook text, and do not treat the textbook's conclusions as conclusions verified by modern science.

## Citation

> Kuang, C. (2026). Foundation Textbook of the Four Pillars and Eight Characters (Version 1.0.0). Zenodo. https://doi.org/10.5281/zenodo.24549949

Use the DOI above for the whole work; for a single lesson you may give the lesson number and the page address, for example:

> Jiayanyide. Foundation Textbook of the Four Pillars and Eight Characters: Lesson 8, Assigning the ten gods[EB/OL]. v1.0.0. (2026-11-26) [2026-11-26]. https://bazi-textbook.jiayanyide.com/textbook/L08/.

For formats other than Chinese, follow the citation text given on the Zenodo record page; whichever format you use, keep the DOI and the lesson number cited.

## Ownership of copyright

Copyright belongs to the author, Kuang Chujia. The licences below grant permission to use, not a transfer of copyright; a licence does not change the author's identity and does not imply that the author endorses the views or products of a user.

## Tiered licensing

Not all files in the textbook use the same licence. They are listed by file category below; there is no single unified LICENSE:

| Content | Scope | Licence (SPDX) |
|---|---|---|
| Main text of the textbook | `docs/textbook/L01.md`—`L17.md` | CC BY-NC-SA-4.0 |
| Practice exercises | `docs/exercises/` | CC BY-NC-SA-4.0 |
| Appendix data | `docs/appendix-data/*.csv` | CC BY-4.0 |
| Self-written scripts | `scripts/` | MIT |

Key points:

- **CC BY-NC-SA 4.0**: attribution, non-commercial use, share alike for adaptations. Commercial use requires a separate licence.
- **CC BY 4.0**: use with attribution, including commercial use, applying to the four structured data files (the sixty jiazi, the ten gods, the twelve stages of growth and decline, the spirits and stars).
- **MIT**: applies to the build and export scripts.

The detailed terms are governed by [RIGHTS.md](https://github.com/Kuangchujia/bazi-textbook/blob/main/RIGHTS.md) in the repository. When quoting third parties, please also mark the layer to which the quoted content belongs.

## Limits of use

- Reproduction and adaptation must credit "Jiayanyide (Kuang Chujia)" and state the version and DOI.
- It is not permitted to alter the text and still publish it under the name of this textbook; a changed version must be marked as changed.
- It is not permitted to use this textbook in a commercial service of specific fortune-telling, or to imply that the author endorses its conclusions.
- The textbook belongs to traditional fate theory, is not claimed to have been confirmed by modern science, and does not constitute medical, legal or investment advice.

## Corrections

Typos, discrepancies in quotations or internal contradictions may be reported through the [GitHub repository](https://github.com/Kuangchujia/bazi-textbook/issues), or by email or WeChat as listed in [Contact and corrections](contact.md). Confirmed corrections are handled with version updates; the original sentences of the main text are not silently altered. Any change to the main text gets a new version number; v1.0.0 is not overwritten in place.
