# -*- coding: utf-8 -*-
"""
场景图库索引构建 — 图存外部路径，只建索引；可选压缩副本入库
用法:
  python build_index.py --root "D:\\场景图库"             # 扫描全部子文件夹，生成 index.yaml
  python build_index.py --root "D:\\场景图库" --repo      # 同时把 2048px 压缩版存进 scenes/（供 git 仓库上传）
  python build_index.py --add "D:\\某图\\某图.jpg" --repo  # 单独追加一张图
产物:
  scene-library/index.yaml          索引（场景id/原图路径/尺寸/色彩统计/自动季节提示）
  scene-library/scenes/<地点>/<id>.jpg  压缩副本（仅 --repo 时）
纯标准库 + PIL。
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from PIL import Image

LIB = Path(__file__).parent
SCENES = LIB / "scenes"
INDEX = LIB / "index.yaml"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_PX = 2048
# 按地点覆盖长边上限：库尔德宁自 2026-11-19 起存原生 4K
MAX_PX_BY_LOCATION = {"库尔德宁": 3840}
# 按地点覆盖输出格式：库尔德宁存无损 PNG
EXT_BY_LOCATION = {"库尔德宁": ".png"}
EXCLUDE_DIRS = {"A2.1真实视频"}  # 不入库的文件夹（视频素材等）


def stats(img):
    rgb = img.convert("RGB")
    w, h = rgb.size
    thumb = rgb.resize((96, 96))
    px = list(thumb.getdata())
    n = len(px)
    lum = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px) / n
    warm = sum(p[0] - p[2] for p in px) / n
    sat = sum(max(p) - min(p) for p in px) / n
    sky = rgb.crop((0, 0, w, h // 3)).resize((24, 24))
    sp = list(sky.getdata())
    sr = sum(p[0] for p in sp) / len(sp)
    sg = sum(p[1] for p in sp) / len(sp)
    sb = sum(p[2] for p in sp) / len(sp)
    ground = rgb.crop((0, 2 * h // 3, w, h)).resize((24, 24))
    gp = list(ground.getdata())
    gr = sum(p[0] for p in gp) / len(gp)
    gg = sum(p[1] for p in gp) / len(gp)
    gb = sum(p[2] for p in gp) / len(gp)
    hints = []
    if gg > gr and gg > gb:
        hints.append("植被绿")
    if gr > 140 and gg > 110 and gb < 110:
        hints.append("暖黄(秋/夕)")
    if lum > 190 and sat < 30 and sr > 190:
        hints.append("雪白(冬)")
    tone = "偏暖" if warm > 8 else "偏冷" if warm < -8 else "中性"
    return dict(size=f"{w}x{h}", lum=round(lum), tone=tone, warm=round(warm),
                sat=round(sat), sky=f"#{int(sr):02x}{int(sg):02x}{int(sb):02x}",
                ground=f"#{int(gr):02x}{int(gg):02x}{int(gb):02x}",
                season_hint=hints or ["常规"])


def slug(name: str) -> str:
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:6]
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)[:40]
    return f"{safe}-{h}"


def process(img_path: Path, do_repo: bool):
    img = Image.open(img_path)
    s = stats(img)
    sid = slug(f"{img_path.parent.name}/{img_path.stem}")
    entry = dict(id=sid, source=f"{img_path.parent.name}/{img_path.name}", folder=img_path.parent.name,
                 file=img_path.name, **s)
    if do_repo:
        location = img_path.parent.name
        for suffix in ("春夏", "秋冬", "秋", "冬"):
            if location.endswith(suffix) and len(location) > len(suffix):
                location = location.removesuffix(suffix).rstrip("-")
                break
        dst_dir = SCENES / location
        dst_dir.mkdir(parents=True, exist_ok=True)
        c = img.convert("RGB")
        max_px = MAX_PX_BY_LOCATION.get(location, MAX_PX)
        c.thumbnail((max_px, max_px), Image.LANCZOS)
        suffix = EXT_BY_LOCATION.get(location, ".jpg")
        c.save(dst_dir / f"{sid}{suffix}", quality=90)
        entry["repo_copy"] = f"scenes/{location}/{sid}{suffix}"
    return entry


def write_index(entries):
    lines = [
        "# 场景图库索引 — 大图只存 GitHub 公开仓库 bebxwbidh/scene-library，本文件是目录",
        "# AI 选景：按 folder(地名)/tone/season_hint 筛 → 目检 thumbs/<id>.jpg → 用 fetch_ref.py --lib scene --id <id> 拉大图喂 gen.py -i",
        "# origin 字段仅为建库出处记录（任何机器上都不存在），禁止当路径使用",
        "",
    ]
    by_folder = {}
    for e in entries:
        by_folder.setdefault(e["folder"], []).append(e)
    for folder, es in sorted(by_folder.items()):
        lines.append(f"## {folder} ({len(es)} 张)")
        for e in es:
            lines.append(f"- id: {e['id']}")
            lines.append(f"  origin: {e['source']}")
            lines.append(f"  size: {e['size']}  tone: {e['tone']}  sat: {e['sat']}  hint: {e['season_hint']}")
            if e.get("repo_copy"):
                lines.append(f"  repo_copy: {e['repo_copy']}")
        lines.append("")
    INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"索引已写入 {INDEX}（共 {len(entries)} 张，{len(by_folder)} 个文件夹）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="扫描根目录")
    ap.add_argument("--add", help="追加单张图")
    ap.add_argument("--repo", action="store_true", help="同时生成 2048px 压缩副本到 scenes/")
    args = ap.parse_args()
    entries = []
    if INDEX.exists():
        cur = INDEX.read_text(encoding="utf-8")
        entries = [e for e in json.loads("[]")]  # 简化：每次全量重建
    if args.add:
        entries.append(process(Path(args.add), args.repo))
    elif args.root:
        root = Path(args.root)
        if not root.exists():
            print(f"路径不存在: {root}")
            return
        files = [p for p in sorted(root.rglob("*"))
                 if p.is_file() and p.suffix.lower() in IMG_EXT
                 and not (set(p.relative_to(root).parts[:-1]) & EXCLUDE_DIRS)]
        print(f"扫描到 {len(files)} 张图")
        for i, p in enumerate(files, 1):
            try:
                entries.append(process(p, args.repo))
                if i % 20 == 0:
                    print(f"  ... {i}/{len(files)}")
            except Exception as ex:
                print(f"  跳过 {p.name}: {ex}")
    else:
        print(__doc__)
        return
    write_index(entries)
    print(f"耗时提示：下次全量重建即可刷新索引；新图追加用 --add。")


if __name__ == "__main__":
    main()
