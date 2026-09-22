"""把 Typst 論文轉成 LaTeX —— 為什麼是「轉」而不是「重寫一份」。

工具事實（實測，不是推測）：
  pandoc 具備 Typst *reader*（本機 3.9.0.2、筆電 3.7.0.2），
  但直接餵完整論文會失敗：
      paper_en.typ (line 474, column 2): unexpected end of input
      Counter does not have a method "get" or FieldAccess requires a dictionary
  原因是它只讀「內容」，不執行版面層——#import 本地套件、
  #show: arxiv-style.with(...) 這種東西它解不了。

  把版面層拿掉、只留內容層之後，轉換品質很好：章節、粗體、條列、
  $數學$、booktabs 表格、甚至 image() 都會正確產出。

所以流程是：
  1. 抽掉版面層（#import / #show / #include / 標題區 / 參考文獻區）
  2. pandoc -f typst -t latex
  3. 一組明確且可稽核的修正
  4. 套上 LaTeX 前言（英文用 kourgeorge/arxiv-style 的原始 arxiv.sty；
     中文用 ctexart + xelatex）

兩條防線，避免「轉出來看起來對、其實數字錯了」：
  * 引用鍵一律對照 refs.bib 白名單；不認得的 {[}...{]} 原樣保留並印出警告。
  * 標題／作者／副標這種短字串若在 Typst 原始檔裡找不到就中止（fail closed）。

用法：python make_latex.py
輸出：paper.tex（英文）、paper_zh.tex（中文）、tables/*.tex
"""
import pathlib
import re
import subprocess
import sys

B = chr(92)                      # 反斜線。用 chr() 寫，避免在原始碼裡堆 escape。
TABLE_TOKEN = "QBNTABLEINPUT"    # 表格 include 的暫時記號（見 strip_layout）
TABLE_INPUTS = []                # 記號 -> 真正的表格路徑
LBR, RBR = re.escape("["), re.escape("]")

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]           # .../QBN
BIB = HERE / "refs.bib"

# arXiv 的 submit_tex 頁面明文建議不要在 \date 裡用 \today：
# 「Because pdf are occasionally rebuilt this date will change and may cause confusion」。
# arxiv.sty 的 \@date 預設就是 \today，所以這裡固定成常數 —— 投稿前改這一行。
PAPER_DATE = "2026-09-21"


DROP_FIELDS = ("note", "annote", "abstract", "keywords", "file")


def strip_fields(text: str, drop) -> str:
    """把 BibTeX 的某些欄位整段拿掉（含跨行的內容）。

    為什麼需要：ieeetr 這個 .bst 會把 note 印進參考文獻，Typst 的 ieee CSL 不會。
    refs.bib 的 note 是我們自己的工作註記（中文、含「TODO(核實)」「★」等字樣），
    不處理的話 LaTeX 版的參考文獻會多出這些東西，兩份 PDF 就不一致了 ——
    而且 arXiv 上的 PDF 會直接出現「TODO」字樣（實測：LaTeX 版 6 處、Typst 版 0 處）。
    """
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        m = re.match("[ ]*([A-Za-z]+)[ ]*=", lines[i])
        if m and m.group(1).lower() in drop:
            depth = 0
            while i < len(lines):
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
                if depth <= 0:
                    break
            if i < len(lines) and lines[i].strip() == ",":
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return chr(10).join(out)


def write_refs_public() -> pathlib.Path:
    out = HERE / "refs_public.bib"
    out.write_text(strip_fields(BIB.read_text(encoding="utf-8"), set(DROP_FIELDS)),
                   encoding="utf-8")
    print("  寫出 refs_public.bib（拿掉欄位：" + ", ".join(DROP_FIELDS) + "）")
    return out


def find_arxiv_sty() -> pathlib.Path:
    """arxiv.sty 是 kourgeorge/arxiv-style 的原始檔，跟 Typst 移植版放在一起。"""
    for cand in (REPO / "packages" / "latex-arxiv-style" / "arxiv.sty",
                 HERE / "arxiv.sty"):
        if cand.exists():
            return cand
    raise SystemExit("找不到 arxiv.sty（packages/latex-arxiv-style/ 底下應有一份）")


def bib_keys() -> set:
    return set(re.findall("[@]" + "[A-Za-z]+" + "[{]([^,]+),", BIB.read_text(encoding="utf-8"), re.M))


INCLUDE_RE = re.compile('#include ' + chr(34) + '((tables)/[A-Za-z0-9_]+)[.]typ' + chr(34))


def strip_layout(text: str) -> str:
    """拿掉 Typst 的版面層，只留內容層，讓 pandoc 讀得動。"""
    lines, out, i = text.splitlines(), [], 0
    while i < len(lines):
        s = lines[i].strip()
        m = INCLUDE_RE.match(s)
        if m:
            # 表格是另一支程式產生的 .tex，這裡先放一個不會被 pandoc 動到的記號，
            # 轉完再換回 input{}。直接丟掉 include 的話，論文會「安靜地」少了表格。
            out.append(table_token(m.group(1)))
            i += 1
            continue
        if s.startswith("#import ") or s.startswith("#include "):
            i += 1
            continue
        if s.startswith("#show: arxiv-style"):
            depth = 0
            while i < len(lines):
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
                if depth <= 0:
                    break
            continue
        out.append(lines[i])
        i += 1
    return chr(10).join(out)


def slice_between(text: str, start_marker: str, end_marker: str) -> str:
    a = text.find(start_marker)
    if a < 0:
        raise SystemExit("原始檔裡找不到起點：" + start_marker)
    b = text.find(end_marker, a)
    return text[a:b if b >= 0 else len(text)]


def bracket_block(text: str, marker: str) -> str:
    """取出 marker 之後第一個 [...] 的內容，支援嵌套。"""
    a = text.find(marker)
    if a < 0:
        raise SystemExit("原始檔裡找不到：" + marker)
    i = text.index("[", a)
    depth, j = 0, i
    while j < len(text):
        if text[j] == "[":
            depth += 1
        elif text[j] == "]":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
        j += 1
    raise SystemExit("括號沒有配對：" + marker)


def paren_block(text: str, marker: str) -> str:
    """取出 marker 之後第一個 (...) 的內容，支援嵌套。keywords 是括號不是方括號。"""
    a = text.find(marker)
    if a < 0:
        raise SystemExit("原始檔裡找不到：" + marker)
    i = text.index("(", a)
    depth, j = 0, i
    while j < len(text):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
        j += 1
    raise SystemExit("括號沒有配對：" + marker)


def fix_subscript_parens(tex: str) -> str:
    """pandoc 的 Typst reader 在 `_` 與 `(` 之間沒有空白時，會把括號吸進下標：

        $R_Y(theta)$   ->  \(R_{Y(\theta)}\)    （錯）
        $R_Y (theta)$  ->  \(R_{Y}(\theta)\)    （對）

    實測 pandoc 3.7.0.2（筆電）與 3.9.0.2（本機）行為一致；Typst 本身的渲染是
    正確的，只有 -t latex 這一步出錯。這裡把 \(_{X(...)}\) 還原成 \(_{X}(...)\)。
    只處理單一字母下標、且括號內不含大括號或括號的情形；若有殘留就 SystemExit
    失敗（fail-closed），絕不靜默產出錯誤的數學式。
    """
    out = re.sub(r"_\{([A-Za-z])\(([^{}()]*)\)\}",
                 lambda m: "_{" + m.group(1) + "}(" + m.group(2) + ")",
                 tex)
    left = re.findall(r"_\{[A-Za-z]\(", out)
    if left:
        raise SystemExit("fix_subscript_parens：仍有未還原的下標 " + repr(left[:5]))
    return out

def to_latex(typst_src: str) -> str:
    proc = subprocess.run(["pandoc", "-f", "typst", "-t", "latex"],
                          input=typst_src, capture_output=True, text=True,
                          encoding="utf-8")
    if proc.returncode != 0:
        raise SystemExit("pandoc 失敗：" + chr(10) + proc.stderr)
    return fix_subscript_parens(proc.stdout)


def fix_figures(tex: str) -> str:
    """includesvg 需要 inkscape 與 shell-escape；我們已經產生向量 PDF，
    改用 LaTeX 原生就吃得下的 includegraphics。"""
    # 收尾是大括號不是方括號 —— 這裡一開始寫成 RBR，圖就永遠轉不掉，
    # 編譯時才以 "Undefined control sequence \includesvg" 爆出來。
    # 參數是 [opts]，但路徑是 {path} —— 兩者不同。這裡先後寫錯過兩次
    # （先寫成 RBR 收尾、再寫成 LBR 開頭），所以下面附一段自我檢查。
    pat = re.compile(re.escape(B + "includesvg") + LBR + "[^]]*" + RBR +
                     "[{]([^}]+)[.]svg[}]")
    assert pat.search(B + "includesvg[a]{b.svg}"), "fix_figures 的樣式對不上實際輸出"
    assert not pat.search(B + "includesvg[a]{b.png}"), "fix_figures 不該動到非 svg"
    def repl(m):
        return B + "includegraphics[width=" + B + "linewidth]{" + m.group(1) + ".pdf}"

    return pat.sub(repl, tex)


def fix_citations(tex: str, keys: set) -> tuple:
    """{[}key{]} 只在使用者白名單（refs.bib 的鍵）內才轉成 cite{}；
    其餘（例如 texttt 裡的切片語法）原樣保留並回報。"""
    unknown = []
    pat = re.compile("[{]" + LBR + "}([A-Za-z][A-Za-z0-9_:.-]*)[{]" + RBR + "}")

    def repl(m):
        key = m.group(1)
        if key in keys:
            return B + "cite{" + key + "}"
        unknown.append(key)
        return m.group(0)

    return pat.sub(repl, tex), unknown


def fix_refs(tex: str, word_fig: str, word_tbl: str) -> str:
    pat = re.compile("[{]" + LBR + "}(fig|tbl|sec)[{]" + RBR + "}:([A-Za-z0-9_:-]+)")
    words = {"fig": word_fig, "tbl": word_tbl, "sec": ""}

    def repl(m):
        kind, name = m.group(1), m.group(2)
        head = words[kind]
        return (head + "~" if head else "") + B + "ref{" + kind + ":" + name + "}"

    return pat.sub(repl, tex)


def fix_label_placement(tex: str) -> str:
    """pandoc 把標籤放在 figure 環境外面（phantomsection + label）。
    搬進 figure 內部，避免 \\ref 依賴「目前計數器」這種脆弱假設。"""
    pat = re.compile(re.escape(B + "end{figure}") + "[ ]*" + chr(10) + "[ ]*" +
                     re.escape(B + "protect" + B + "phantomsection" + B + "label") +
                     "[{]([^}]+)[}]" + "[{]" + RBR + "}")

    def repl(m):
        return B + "label{" + m.group(1) + "}" + chr(10) + B + "end{figure}"

    return pat.sub(repl, tex)


def table_token(path: str) -> str:
    """表格 include 的暫時記號。刻意只用英數字：pandoc 會把底線轉義成
    backslash-underscore，記號裡只要有不安全字元就會被改到、換不回來
    （這是真的踩到的 bug：capacity_en 變成 capacity 加一段殘留）。"""
    TABLE_INPUTS.append(path)
    return TABLE_TOKEN + str(len(TABLE_INPUTS) - 1).zfill(3)


def fix_include_tokens(tex: str) -> str:
    for i, path in enumerate(TABLE_INPUTS):
        tex = tex.replace(TABLE_TOKEN + str(i).zfill(3),
                          B + "input{" + path + ".tex}")
    return tex


LT_BEGIN = re.compile(re.escape(B + "begin{longtable}[]"))
LT_END = B + "end{longtable}"
LT_RULES = (B + "toprule" + B + "noalign{}",
            B + "midrule" + B + "noalign{}",
            B + "bottomrule" + B + "noalign{}")


def _take_braced(text: str, start: int):
    """從 text[start] 的 { 開始，回傳 (內容, 收尾括號的位置)。"""
    depth, k = 0, start
    while k < len(text):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:k], k
        k += 1
    raise SystemExit("大括號沒有配對")


def _split_longtable(block: str):
    """把 longtable 內容拆成 (caption, header, body)。

    pandoc 會產生兩種形狀：
      A. 有表頭：toprule / 表頭 / midrule / endfirsthead / 表頭 / endhead / ...
      B. 沒表頭：toprule / endhead / ...
    endfirsthead 之後那一份是重複的表頭，丟掉只留一份。
    """
    cap = None
    m = re.search(re.escape(B + "caption") + "[{]", block)
    if m:
        cap, end = _take_braced(block, m.end() - 1)
        block = block[:m.start()] + block[end + 1:]
    block = block.replace(B + "tabularnewline", "")
    header, body, state = [], [], "head"
    for ln in block.splitlines():
        s = ln.strip()
        if s in LT_RULES:
            continue
        if s == B + "endfirsthead":
            state = "drop"
            continue
        if s in (B + "endhead", B + "endlastfoot"):
            state = "body"
            continue
        if state == "head":
            header.append(ln)
        elif state == "body":
            body.append(ln)
    return cap, [h for h in header if h.strip()], [b for b in body if b.strip()]


def _render_table(block: str, cols: str):
    cap, header, body = _split_longtable(block)
    inner = [B + "begin{tabular}{" + cols + "}", B + "toprule"]
    if header:
        inner += header + [B + "midrule"]
    inner += body + [B + "bottomrule", B + "end{tabular}"]
    # 只縮不放：寬度超過版面才縮到 linewidth，否則維持原寬。
    # 不用 adjustbox 是因為本機 MiKTeX 裝不起來（套件庫逾時），
    # 而 graphicx 已經為了 includegraphics 載入，零額外依賴。
    wrapped = ([B + "resizebox{" + B + "ifdim" + B + "width>" + B + "linewidth "
                + B + "linewidth" + B + "else" + B + "width" + B + "fi}{!}{%"]
               + inner + ["}"])
    if cap:
        return ([B + "begin{table}[t]", B + "centering", B + "caption{" + cap + "}"]
                + wrapped + [B + "end{table}", ""])
    return [B + "begin{center}"] + wrapped + [B + "end{center}", ""]


def fix_longtable(tex: str) -> str:
    """把 pandoc 的 longtable 換成 table/tabular + booktabs，並縮到版面寬。

    為什麼非換不可（實測，不是排版偏好）：
      * longtable 的欄位是 l（自然寬度、不換行）。7 欄那張表的第一欄是
        「D depolarising (after encoding)」這種長字串，整張表就衝出頁面右緣
        —— 編譯紀錄是 Overfull hbox 24.36426pt in alignment。
      * 那張表在 Typst 原稿裡沒有 table.header()，pandoc 只能把它當普通資料列，
        於是表頭與資料的欄位對不齊；原稿已補上 table.header()，這裡再把 LaTeX
        端補成正確結構（toprule / 表頭 / midrule / 資料 / bottomrule）。
    做法取自兩篇 arXiv 論文：booktabs 三線表 + 縮到版面寬（2609.20523 用 adjustbox；
    我們改用 graphicx 的 resizebox，零額外依賴），以及固定寬欄位配小字級（2602.04770）。
    """
    lines = tex.splitlines()
    out, i = [], 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("{" + B + "def" + B + "LTcaptype"):
            i += 1
            continue
        m = LT_BEGIN.match(s)
        if not m:
            out.append(lines[i])
            i += 1
            continue
        # 欄位規格可能跨行：有相對寬度的表會用 p{...} 這種寫法，一行一個欄位。
        # 累積到括號平衡為止，再剝掉最外層的大括號。
        # 會一行一個欄位。累積到括號平衡為止，再剝掉最外層的大括號。
        spec = s[m.end():]
        i += 1
        while spec.count("{") != spec.count("}") and i < len(lines):
            spec += " " + lines[i].strip()
            i += 1
        cols = spec.strip()[1:-1]
        block = []
        while i < len(lines) and lines[i].strip() != LT_END:
            block.append(lines[i])
            i += 1
        i += 1
        if i < len(lines) and lines[i].strip() == "}":
            i += 1
        out.extend(_render_table(chr(10).join(block), cols))
    return chr(10).join(out)


TEXTTT_RE = re.compile(re.escape(B + "texttt{") + "([^{}]*)" + re.escape("}"))


def fix_texttt_breaks(tex: str) -> str:
    """\texttt{} 內的檔案路徑是單一不可斷詞，長路徑會撐破行寬造成 overfull hbox。
    在 / 與 _ 之後插入 \allowbreak，給 LaTeX 斷點（不改變顯示出來的內容）。"""

    def repl(m: "re.Match") -> str:
        body = m.group(1)
        body = body.replace("/", "/" + B + "allowbreak ")
        body = body.replace("_", "_" + B + "allowbreak ")
        return B + "texttt{" + body + "}"

    return TEXTTT_RE.sub(repl, tex)


def fix_tables(tex: str) -> str:
    return tex.replace(" +/- ", " $" + B + "pm$ ")


def macro_lines(text: str) -> str:
    """Typst 的自訂數學巨集（#let ket(x) = [|#x⟩] 這類）。pandoc 會真的求值它們，
    但我們把內容切片出來時，定義在檔頭的巨集也一起被切掉了，所以要單獨撿回來。
    少了這一步會出現 Identifier "ket" not found —— 這是實測到的失敗，不是推測。"""
    keep = []
    for line in text.splitlines():
        if not line.startswith("#let "):
            continue
        # 只收「單行就寫完」的定義。跨行的（例如
        #   #let paper-margin = if style == "arxiv" {
        # 後面還有好幾行）只撿第一行會得到語法不完整的片段，
        # pandoc 會直接死在 unexpected "#"。用括號是否平衡來判斷。
        if (line.count("{") != line.count("}")
                or line.count("(") != line.count(")")
                or line.count("[") != line.count("]")):
            continue
        keep.append(line)
    return chr(10).join(keep)


def convert_tables(keys: set) -> None:
    for src in sorted((HERE / "tables").glob("*.typ")):
        out = src.with_suffix(".tex")
        body = to_latex(strip_layout(src.read_text(encoding="utf-8")))
        body, unknown = fix_citations(body, keys)
        body = fix_longtable(fix_tables(fix_figures(body)))
        if unknown:
            print("  警告：表格", src.name, "有無法辨識的引用", unknown)
        out.write_text(body, encoding="utf-8")
        print("  寫出", out.name, len(body.splitlines()), "行")


def en_metadata(src: str) -> dict:
    title = re.search("title: " + chr(34) + "([^" + chr(34) + "]+)" + chr(34), src)
    if not title:
        raise SystemExit("英文版：找不到 title:")
    block = bracket_block(src, "abstract: ")
    kw = paren_block(src, "keywords: (") if "keywords: (" in src else ""
    authors = re.findall("name: " + chr(34) + "([^" + chr(34) + "]+)" + chr(34), slice_between(src, "authors: (", "affiliations: ("))
    affils = re.findall("[(]id: " + "[0-9]+, name: " + chr(34) + "([^" + chr(34) + "]+)" + chr(34), src)
    return {"title": title.group(1), "abstract": block,
            "authors": authors, "affiliations": affils,
            "keywords": re.findall(chr(34) + "([^" + chr(34) + "]+)" + chr(34), kw)}


def affil_parbox(affil: str) -> str:
    """\author{} 的每一行都是一個不可斷的 hbox，單位太長就會 overfull。
    放進 \parbox 讓它自然斷行；並在「通訊作者」之前強制換行。"""
    marker = ". Corresponding author:"
    if marker in affil:
        affil = affil.replace(marker, "." + B + B + "Corresponding author:")
    return B + "parbox{0.86" + B + "textwidth}{" + B + "centering " + affil + "}"


def build_en(keys: set) -> None:
    src = (HERE / "paper_en.typ").read_text(encoding="utf-8")
    meta = en_metadata(src)
    body = macro_lines(src) + chr(10) + slice_between(strip_layout(src), "= Introduction", "= References")
    # 順序有講究：先處理 {[}fig{]}:x 這種交互參照，再處理引用。
    # 反過來的話 {[}fig{]} 會先被當成「不認得的引用鍵」而印出誤導性的警告。
    tex = fix_refs(fix_figures(to_latex(body)), "Figure", "Table")
    tex, unknown = fix_citations(tex, keys)
    tex = fix_texttt_breaks(fix_longtable(fix_include_tokens(fix_tables(fix_label_placement(tex)))))
    if unknown:
        print("  警告：英文版有無法辨識的 {[}...{]}：", sorted(set(unknown)))

    auth = (" " + B + B + chr(10) + "  " + B + "And" + chr(10)).join(meta["authors"]) \
        + " " + B + B + chr(10) + "  " + affil_parbox(meta["affiliations"][0])

    head = chr(10).join([
        "% 這份檔案由 make_latex.py 產生，不要直接手改；請改 paper_en.typ。",
        B + "documentclass{article}",
        B + "usepackage{arxiv}",
        B + "usepackage[utf8]{inputenc}",
        B + "usepackage[T1]{fontenc}",
        B + "usepackage{hyperref}",
        B + "hypersetup{colorlinks=true,linkcolor=black,citecolor=[rgb]{0,0.31,0.62},urlcolor=[rgb]{0,0.31,0.62}}",
        B + "usepackage{url}",
        B + "usepackage{booktabs}",
        B + "usepackage{longtable}",
        # pandoc 會把 Typst 的 op("CX") 轉成 operatorname{}，那是 amsmath 的東西。
        B + "usepackage{amsmath}",
        # pandoc 的 longtable 欄寬有三個依賴，缺一都會以 Undefined control sequence 爆掉：
        #   array    -> >{...} 與 arraybackslash（本檔一開始就是漏了它）
        #   calc     -> (...) * real{0.3333} 的長度算術
        # real 由 calc 提供；下面再 providecommand 一次，calc 已定義時是 no-op，
        # 當成保險（換 TeX 發行版時不會突然編不過）。
        B + "usepackage{array}",
        B + "usepackage{calc}",
        B + "providecommand{" + B + "real}[1]{#1}",
        B + "usepackage{amsfonts}",
        B + "usepackage{nicefrac}",
        B + "usepackage{microtype}",
        B + "usepackage{graphicx}",
        B + "usepackage[numbers,sort&compress]{natbib}",
        "",
        B + "title{" + meta["title"] + "}",
        B + "author{" + auth + "}",
        B + "date{" + PAPER_DATE + "}",
        B + "renewcommand{" + B + "shorttitle}{" + meta["title"] + "}",
        B + "hypersetup{pdftitle={" + meta["title"] + "},"
        "  pdfkeywords={" + ", ".join(meta["keywords"]) + "}}",
        "",
        B + "begin{document}",
        B + "maketitle",
        "",
        B + "begin{abstract}",
        to_latex(meta["abstract"]).strip(),
        B + "end{abstract}",
        "",
        # 注意：B + "and ".join(x) 會先 join 再接反斜線（優先序陷阱），
        # 一定要把 B + "and " 整個括起來。
        B + "keywords{" + (B + "and ").join(meta["keywords"]) + "}",
        "",
    ])
    tail = chr(10).join(["", B + "bibliographystyle{apsrev4-2}", B + "bibliography{refs_public}", "", B + "end{document}", ""])
    (HERE / "paper.tex").write_text(head + tex + tail, encoding="utf-8")
    print("  寫出 paper.tex", len(tex.splitlines()), "行正文")


ZH_TITLE = "量子分類器的容量斷崖與校準消融"
ZH_SUBTITLE = "Capacity Cliff and Calibration Ablation in a Hybrid Quantum--Classical Classifier"
ZH_AUTHORS = "Xin Yang、Poyuan Chung、Yuan-Liang Zhong"
ZH_AFFIL = "中原大學物理系（Department of Physics, Chung Yuan Christian University），台灣桃園"
ZH_CHECK = (
    ZH_TITLE,
    ZH_SUBTITLE,
    "Poyuan Chung",
    "Xin Yang",
    "Yuan-Liang Zhong",
    ZH_AFFIL,
)


def build_zh(keys: set) -> None:
    src = (HERE / "paper.typ").read_text(encoding="utf-8")
    # fail closed：這些字串是我們在 LaTeX 標題區「重打」的，一旦 Typst 那邊改了、
    # 這裡沒跟著改，兩份 PDF 的標題就會不一致 —— 寧可中止也不要默默不一致。
    for needle in ZH_CHECK:
        if needle not in src:
            raise SystemExit("中文版：paper.typ 裡找不到 " + repr(needle) + "，請同步 make_latex.py 的 ZH_* 常數")
    abstract = to_latex(bracket_block(src, "#block(inset: (x: 1.2em))[")).strip()
    marker = B + "textbf{摘要}——"
    if abstract.startswith(marker):
        abstract = abstract[len(marker):].strip()
    body = macro_lines(src) + chr(10) + slice_between(strip_layout(src), "= 引言", "= 參考文獻")
    tex = fix_refs(fix_figures(to_latex(body)), "圖", "表")
    tex, unknown = fix_citations(tex, keys)
    tex = fix_texttt_breaks(fix_longtable(fix_include_tokens(fix_tables(fix_label_placement(tex)))))
    if unknown:
        print("  警告：中文版有無法辨識的 {[}...{]}：", sorted(set(unknown)))

    head = chr(10).join([
        "% 這份檔案由 make_latex.py 產生，不要直接手改；請改 paper.typ。",
        "% 中文排版用 ctexart + xelatex（見 build_tex.bat）。",
        B + "documentclass[11pt,a4paper]{ctexart}",
        B + "usepackage[margin=2.4cm]{geometry}",
        B + "usepackage{amsmath,amssymb}",
        B + "usepackage{calc}",
        B + "usepackage{graphicx}",
        B + "usepackage{booktabs}",
        B + "usepackage{longtable}",
        B + "usepackage{array}",
        B + "usepackage[numbers]{natbib}",
        B + "usepackage{hyperref}",
        B + "hypersetup{colorlinks=true,linkcolor=black,citecolor=[rgb]{0,0.31,0.62},urlcolor=[rgb]{0,0.31,0.62}}",
        "% CJK 段落常因缺少斷行點而溢出邊界；放寬斷行伸縮量（只影響間距，不影響內容）。",
        B + "emergencystretch=3em",
        "",
        B + "title{" + ZH_TITLE + B + B + "[0.35em]" + B + "large " + ZH_SUBTITLE + "}",
        B + "author{" + ZH_AUTHORS + B + B + affil_parbox(ZH_AFFIL) + "}",
        B + "date{}",
        "",
        B + "begin{document}",
        B + "maketitle",
        "",
        B + "begin{abstract}",
        abstract,
        B + "end{abstract}",
        "",
    ])
    tail = chr(10).join(["", B + "bibliographystyle{apsrev4-2}", B + "bibliography{refs_public}", "", B + "end{document}", ""])
    (HERE / "paper_zh.tex").write_text(head + tex + tail, encoding="utf-8")
    print("  寫出 paper_zh.tex", len(tex.splitlines()), "行正文")


def main() -> int:
    style = find_arxiv_sty()
    keys = bib_keys()
    print("arxiv.sty:", style, "| refs.bib 鍵數:", len(keys))
    print("產生 LaTeX 用的參考文獻：")
    write_refs_public()
    print("轉換表格：")
    convert_tables(keys)
    print("轉換英文版：")
    build_en(keys)
    print("轉換中文版：")
    build_zh(keys)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
