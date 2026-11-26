# -*- coding: utf-8 -*-
"""P0-1：冻结现有二十件原始导出，记录大小与 SHA256。"""
import os, shutil, hashlib, datetime

SRC = r'D:\OneDrive\文档\Obsidian Vault\术数网\code\八字栏目\open_bazi_repo'
DST = os.path.join(SRC, '_frozen_20261126')

items = []
for fn in ['00-说明.md', 'manifest.json', '练习题手册·无答案.md']:
    items.append(fn)
for n in range(1, 18):
    items.append(os.path.join('lessons', 'lesson-%02d.md' % n))

lines = []
for rel in items:
    src = os.path.join(SRC, rel)
    assert os.path.exists(src), src
    dst = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    b = open(src, 'rb').read()
    h = hashlib.sha256(b).hexdigest()
    assert hashlib.sha256(open(dst, 'rb').read()).hexdigest() == h
    lines.append((rel.replace('\\', '/'), len(b), h))

sums = os.path.join(SRC, 'SHA256SUMS_original.txt')
with open(sums, 'w', encoding='utf-8', newline='\n') as f:
    for rel, size, h in lines:
        f.write('%s  %s (%d bytes)\n' % (h, rel, size))

receipt = os.path.join(SRC, 'FREEZE_RECEIPT.md')
with open(receipt, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 原始导出冻结回执\n\n')
    f.write('冻结时间：%s\n\n' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    f.write('对象：十七课 Markdown、manifest.json、00-说明.md、练习题手册·无答案.md，共 %d 件。\n' % len(lines))
    f.write('冻结目录：`_frozen_20261126/`，原件未覆盖。逐件 SHA256 见 `SHA256SUMS_original.txt`。\n\n')
    f.write('| 文件 | 字节 | SHA256（前 16 位） |\n|---|---:|---|\n')
    for rel, size, h in lines:
        f.write('| `%s` | %d | `%s` |\n' % (rel, size, h[:16]))
    f.write('\n本回执只记事实，不对原文作任何改动。\n')

print('frozen', len(lines), 'files;', sum(x[1] for x in lines), 'bytes')
print('receipt', receipt)
