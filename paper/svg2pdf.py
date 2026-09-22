r"""svg2pdf.py -- 把 figs/*.svg 轉成同尺寸的 PDF（LaTeX 管線需要 PDF）。

Typst 的 #set page 必須與圖的長寬比一致，否則產出會是預設 A4 直式，
在 LaTeX 裡 width=\linewidth 會被放大成超過 textheight 的高度，
引發 "Float too large for page" 警告（本專案曾發生：tau_dose.pdf 是 A4）。
"""
import pathlib, re, subprocess, sys, tempfile

PAPER = pathlib.Path(r"C:\Users\qq134\source\repos\QBN\projects\qbn-capacity-calibration\paper")
FIGS = PAPER / "figs"


def svg_aspect(svg: pathlib.Path):
    head = svg.read_text(encoding="utf-8", errors="replace")[:600]
    m = re.search(r'viewBox="[\d.\- ]*?([\d.]+)[ ,]+([\d.]+)"', head)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r'width="([\d.]+)[a-z]*"[^>]*height="([\d.]+)', head)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


def convert(svg: pathlib.Path, width_mm: float = 240.0) -> bool:
    asp = svg_aspect(svg)
    if not asp:
        print("  !! %s: 讀不到尺寸" % svg.name)
        return False
    w, h = asp
    height_mm = width_mm * h / w
    src = (PAPER / "_svg2pdf.typ")
    src.write_text(
        "#set page(width: %.2fmm, height: %.2fmm, margin: 0pt)\n#image(\"%s\", width: 100%%)\n"
        % (width_mm, height_mm, "figs/" + svg.name),
        encoding="utf-8", newline="\n")
    r = subprocess.run(["typst", "compile", "--root", ".", "_svg2pdf.typ",
                        "figs/" + svg.stem + ".pdf"],
                       cwd=str(PAPER), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    src.unlink(missing_ok=True)
    out = FIGS / (svg.stem + ".pdf")
    if r.returncode != 0 or not out.exists():
        print("  !! %s 轉換失敗: %s" % (svg.name, (r.stderr or "")[:200]))
        return False
    raw = out.read_bytes()
    mb = re.findall(rb"/MediaBox\s*\[([^\]]*)\]", raw)
    box = ""
    if mb:
        v = [float(x) for x in mb[0].split()]
        box = "%.1f x %.1f pt" % (v[2] - v[0], v[3] - v[1])
    print("  %-18s %.1f x %.1f mm  ->  MediaBox %s" % (svg.name, width_mm, height_mm, box))
    return True


if __name__ == "__main__":
    names = sys.argv[1:] or ["tau_dose.svg"]
    for n in names:
        convert(FIGS / n)