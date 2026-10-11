# -*- coding: utf-8 -*-
"""从 arabic_book_complete_zh.md 生成 7 个单元 HTML 页面（阿中对照 + 发音标记）。"""
import re, html, os

SRC = r"C:\Users\迪丽希斯\OneDrive\Desktop\arabic_book_complete_zh.md"
OUT = r"D:\workbuddy工作区\2026-10-11-21-27-02\arabic-between-hands"

AR_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')

def wrap_ar(s):
    def repl(m):
        run = m.group(0)
        attr = html.escape(run, quote=True)
        return '<span class="ar" data-ar="%s">%s</span>' % (attr, run)
    return AR_RE.sub(repl, s)

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<em>\1</em>', s)
    s = wrap_ar(s)
    return s

def cells(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    return [c.strip() for c in line.split("|")]

def render_table(rows):
    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    th = "".join("<th>%s</th>" % inline(c) for c in header)
    trs = []
    for r in body:
        tds = []
        for c in r:
            cls = ' class="ar-cell"' if AR_RE.search(c) else ''
            tds.append("<td%s>%s</td>" % (cls, inline(c)))
        trs.append("<tr>%s</tr>" % "".join(tds))
    return ('<table class="content-table"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table>' % (th, "".join(trs)))

def md_to_html(md):
    lines = md.split("\n")
    n = len(lines)
    blocks = []
    i = 0
    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1; continue
        st = line.lstrip()
        # table
        if st.startswith("|") and i + 1 < n and re.match(r'^\s*\|?[\s:|-]+\|?\s*$', lines[i+1]):
            tbl = [line]
            i += 1
            i += 1  # skip separator
            while i < n and lines[i].lstrip().startswith("|"):
                tbl.append(lines[i]); i += 1
            blocks.append(("table", tbl)); continue
        # blockquote
        if st.startswith(">"):
            bq = []
            while i < n and lines[i].lstrip().startswith(">"):
                bq.append(lines[i].lstrip()[1:].strip()); i += 1
            blocks.append(("quote", bq)); continue
        if st.startswith("#### "):
            blocks.append(("h4", st[5:].strip())); i += 1; continue
        if st.startswith("### "):
            blocks.append(("h3", st[4:].strip())); i += 1; continue
        if st.startswith("## "):
            blocks.append(("h2", st[3:].strip())); i += 1; continue
        # paragraph
        para = []
        while (i < n and lines[i].strip() != ""
               and not lines[i].lstrip().startswith(("|", ">", "#"))):
            para.append(lines[i].strip()); i += 1
        blocks.append(("p", para)); continue

    out = []
    for kind, data in blocks:
        if kind == "h2":
            out.append("<h2>%s</h2>" % inline(data))
        elif kind == "h3":
            out.append("<h3>%s</h3>" % inline(data))
        elif kind == "h4":
            out.append("<h4>%s</h4>" % inline(data))
        elif kind == "quote":
            out.append('<div class="note-box info">%s</div>' %
                       "<br>".join(inline(l) for l in data))
        elif kind == "p":
            txt = " ".join(inline(l) for l in data)
            if re.fullmatch(r'\s*-{3,}\s*', txt.strip()):
                continue
            out.append("<p>%s</p>" % txt)
        elif kind == "table":
            out.append(render_table(data))
    return "\n".join(out)

NAV_ITEMS = [
    ("index.html", "首页"),
    ("unit-1.html", "第一单元"),
    ("unit-2.html", "第二单元"),
    ("unit-3a.html", "第三·日常"),
    ("unit-3b.html", "第三·饮食"),
    ("unit-7.html", "第七·学习"),
    ("unit-3c.html", "第三·职业"),
    ("unit-4.html", "第四·测试"),
    ("grammar.html", "语法总表"),
    ("exercises.html", "练习册"),
]
ORDER = [x[0] for x in NAV_ITEMS]

def nav_links(active):
    parts = []
    for href, label in NAV_ITEMS:
        cls = ' class="active"' if href == active else ''
        parts.append('<a href="%s"%s>%s</a>' % (href, cls, label))
    return "\n        ".join(parts)

def nav_buttons(cur):
    idx = ORDER.index(cur)
    prev_h = ORDER[idx-1] if idx > 0 else None
    next_h = ORDER[idx+1] if idx < len(ORDER)-1 else None
    def btn(href, label, side):
        if not href:
            return '<a class="disabled">%s</a>' % ("← 上一页" if side=="p" else "下一页 →")
        return '<a href="%s">%s</a>' % (href, label)
    p = btn(prev_h, "← 上一页", "p") if prev_h else '<a class="disabled">← 已是首页</a>'
    n = btn(next_h, "下一页 →", "n") if next_h else '<a class="disabled">已是末页 →</a>'
    mid = '<a href="index.html">🏠 返回目录</a>'
    return '<div class="nav-buttons">%s%s%s</div>' % (p, mid, n)

def page_template(meta, body_html, active):
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 《阿拉伯语在你手中》第一册</title>
<link rel="stylesheet" href="css/styles.css">
</head>
<body>
<div class="scroll-progress"></div>

<nav class="top-nav">
  <div class="nav-logo"><span class="ar-logo">العربية</span><span>阿拉伯语在你手中</span></div>
  <button class="nav-toggle">☰</button>
  <div class="nav-links">
        {navlinks}
  </div>
</nav>

<header class="unit-hero">
  <span class="hero-badge">{badge}</span>
  <h1>{title}</h1>
  <div class="ar-title">{ar}</div>
  <p class="subtitle">{desc}</p>
  <div class="hero-tags"><span>阿中对照</span><span>{range}</span><span>点击 🔊 发音</span></div>
</header>

<main>
{body}
</main>

{navbuttons}

<footer class="site-footer">
  <div class="ar-foot">العربية بين يديك</div>
  <div>《阿拉伯语在你手中》العربية بين يديك · 学生用书 第一册（A 分册）</div>
  <div style="margin-top:6px;opacity:.7">Arabic Between Your Hands · Book 1 · 交互式学习网页</div>
</footer>

<script src="js/app.js"></script>
</body>
</html>
""".format(title=meta["title"], badge=meta["badge"], ar=meta["ar"],
           desc=meta["desc"], range=meta["range"],
           navlinks=nav_links(active), body=body_html, navbuttons=nav_buttons(active))

UNITS = [
  {"file":"unit-1.html","badge":"第一单元","title":"问候与相识","ar":"الوحدة الأولى: التحية والتعارف",
   "desc":"学会阿拉伯语最基本的问候、自我介绍与询问他人姓名、国籍，掌握人称代词与指示代词，并完成字母书写入门。",
   "marker":"## 第一单元：问候与相识（","range":"原书页 23–48"},
  {"file":"unit-2.html","badge":"第二单元","title":"家庭","ar":"الوحدة الثانية: الأسرة",
   "desc":"掌握家庭称谓（父/母/兄弟/姐妹/祖父/祖母/叔伯/子女），运用指示代词 هَذَا/هَذِهِ 与所属结构，能介绍家人。",
   "marker":"## 第二单元：家庭（","range":"原书页 49–76"},
  {"file":"unit-3a.html","badge":"第三单元（一）","title":"日常生活 · 住所与作息","ar":"الوحدة الثالثة: الحياة اليومية",
   "desc":"住所与家具词汇、日常作息表达、食物饮料、存在/方位、时间介词与疑问词，并能就住所、作息与饮食问答。",
   "marker":"## 第三单元：日常生活（","range":"原书页 77–142"},
  {"file":"unit-3b.html","badge":"第三单元（二）","title":"食物与饮品 · 礼拜 · 学习","ar":"الوحدة الثالثة: الطعام والشراب",
   "desc":"三餐与饮食、旅行与礼拜、五番拜功、1–10 序数词，并复习日常去向与疑问表达。",
   "marker":"## 第三单元：食物与饮品（","range":"原书页 143–184"},
  {"file":"unit-7.html","badge":"第七单元","title":"学习","ar":"الوحدة السابعة: الدراسة",
   "desc":"星期、学校生活词汇，用序数词表钟点，以及将来时 سَأَكُونُ 的运用。",
   "marker":"## 第七单元：学习（","range":"原书页 185–208"},
  {"file":"unit-3c.html","badge":"第三单元（三）","title":"工作 · 职业 · 自测","ar":"الوحدة الثالثة: العمل والمهن",
   "desc":"职业名称、在何处学习/从事何工作/每天工作几小时，串联前几单元所学并完成全册自测与词汇索引。",
   "marker":"## 第三单元：工作、职业与日常生活（","range":"原书页 209–275"},
  {"file":"unit-4.html","badge":"第四单元","title":"听力与口语测试","ar":"الوحدة الرابعة: فهم المسموع والاختبار الشفهي",
   "desc":"听力理解与口语测试，综合检验学校生活、日常作息、职业工作等前几单元所学。",
   "marker":"## 第四单元：听力与口语测试（","range":"原书页 276–282"},
]

def main():
    with open(SRC, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    positions = {}
    for u in UNITS:
        for idx, ln in enumerate(lines):
            if ln.strip().startswith(u["marker"]):
                positions[u["file"]] = idx
                break
        else:
            print("!! 未找到:", u["marker"])
    # 按文件出现顺序排序切片
    files_sorted = sorted(positions, key=lambda f: positions[f])
    for k, f in enumerate(files_sorted):
        start = positions[f] + 1
        end = positions[files_sorted[k+1]] if k+1 < len(files_sorted) else len(lines)
        chunk = "\n".join(lines[start:end])
        meta = next(u for u in UNITS if u["file"] == f)
        body = md_to_html(chunk)
        html_out = page_template(meta, body, f)
        with open(os.path.join(OUT, f), "w", encoding="utf-8") as w:
            w.write(html_out)
        print("OK", f, "chars=", len(html_out))

if __name__ == "__main__":
    main()
