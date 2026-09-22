"""組出可以整包上傳到 arXiv 的目錄。

為什麼需要這一支（三條都是 arXiv 官方 submit_tex 頁面明文的規定）：

  1. 「compilation is always done from the root of your submission directory」
     —— 但我們本機 build_tex.bat 是用 TEXINPUTS 指向 packages/latex-arxiv-style/，
     那條路徑在 arXiv 上不存在。所以 arxiv.sty 必須被攤平到送出目錄的根。
  2. 「We do not have your style files or macros」
     —— 它只給 TeX Live 裡的東西；自備的 .sty 要自己附上。
  3. 「if you have a file named foo.tex, then do not include any associated
      auxiliary file or intermediate or resulting output file」
     —— .aux/.log/.fls/.xdv/.pdf 都不可以混進去。這裡用白名單複製，天然不違反。

另外兩條：
  * .bbl 的檔名必須跟主檔一致（paper.tex -> paper.bbl），否則參考文獻會掉。
  * 圖片只接受 pdf/png/jpg，而且 arXiv 不做即時轉檔 —— 我們直接給向量 PDF。

做法是「照 paper.tex 實際引用了什麼就複製什麼」：
  多送沒用到的檔案違反 arXiv 的 "tidy your submission"；
  少送則會在 arXiv 上編不過。兩邊都用同一份掃描結果決定，所以不會各說各話。

用法：python make_submission.py [主檔名，預設 paper.tex]
輸出：submission/（或 submission-<主檔名>/）＋ 同名 .zip
"""
import pathlib
import re
import shutil
import sys
import zipfile

B = chr(92)
LBR, RBR = re.escape("["), re.escape("]")

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
STYLE = REPO / "packages" / "latex-arxiv-style" / "arxiv.sty"

INCLUDE_RE = re.compile(re.escape(B + "includegraphics") +
                        "(?:" + LBR + "[^]]*" + RBR + ")?" + "[{]([^}]+)[}]")
INPUT_RE = re.compile(re.escape(B + "input") + "[{]([^}]+)[}]")


def main() -> int:
    stem = sys.argv[1] if len(sys.argv) > 1 else "paper.tex"
    main_tex = HERE / stem
    if not main_tex.exists():
        raise SystemExit("找不到 " + stem + "：先跑 make_latex.py（或 build_tex.bat）")
    name = main_tex.stem
    out = HERE / ("submission" if name == "paper" else "submission-" + name)
    zip_path = out.with_suffix(".zip")

    tex = main_tex.read_text(encoding="utf-8")
    figs = INCLUDE_RE.findall(tex)
    inputs = INPUT_RE.findall(tex)
    if not figs:
        raise SystemExit(stem + " 裡找不到任何 includegraphics —— 先確認轉換有跑成功")

    bbl = HERE / (name + ".bbl")
    if not bbl.exists():
        raise SystemExit("找不到 " + bbl.name + "：arXiv 靠它產生參考文獻，"
                         "先跑一次 latexmk/xelatex 讓 bibtex 產生它")

    # 用 refs_public.bib（make_latex.py 產生，已去掉工作註記）；
    # paper.tex 裡的 bibliography{refs_public} 就是指向它。
    wanted = [main_tex, STYLE, HERE / "refs_public.bib", bbl]
    wanted += [HERE / rel for rel in figs + inputs]
    missing = [w for w in wanted if not w.exists()]
    if missing:
        raise SystemExit("這些檔案被引用但不存在：" + chr(10) + "  " +
                         (chr(10) + "  ").join(str(m) for m in missing))

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for src in wanted:
        # 一律攤平到送出目錄的根；figs/ 與 tables/ 這種子目錄保留原名，
        # 因為 paper.tex 裡的相對路徑就是那樣寫的，而 arXiv 從根開始編譯。
        # arxiv.sty 在 packages/ 底下，不在這個目錄，所以要先試 relative_to。
        try:
            rel = src.relative_to(HERE)
        except ValueError:
            rel = pathlib.Path(src.name)
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(out))

    print("送出目錄：", out)
    for f in sorted(out.rglob("*")):
        if f.is_file():
            print("   %-34s %8d bytes" % (str(f.relative_to(out)), f.stat().st_size))
    print("壓縮檔：", zip_path, zip_path.stat().st_size, "bytes")
    print("缺少的檔案：無（%d 個引用全部命中）" % (len(figs) + len(inputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
