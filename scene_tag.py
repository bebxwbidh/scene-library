# -*- coding: utf-8 -*-
"""
场景图自动打标脚本 — lvpai-wedding-sets scene-library
用法:
  python scene_tag.py                  # 扫描 inbox/ 下所有图，打印色彩统计 + 建议场景 id
  python scene_tag.py --commit <id>    # 把 inbox 里最新一张图入库为 scenes/<id>/scene.jpg
输出统计项（借鉴 gallery-tools/analyze.py 思路，但独立运行、无 CSV 依赖）:
  亮度 / 暖冷倾向 / 饱和度 / 上1/3天空区色彩 / 下1/3地面区色彩
纯标准库 + PIL，不依赖 numpy。
"""
import sys
from pathlib import Path
from PIL import Image

LIB = Path(__file__).parent
INBOX = LIB / "inbox"
SCENES = LIB / "scenes"


def rgb_mean(img, box):
    region = img.crop(box).resize((32, 32))
    px = list(region.getdata())
    n = len(px)
    r = sum(p[0] for p in px) / n
    g = sum(p[1] for p in px) / n
    b = sum(p[2] for p in px) / n
    return r, g, b


def describe(img):
    w, h = img.size
    thumb = img.convert("RGB").resize((128, 128))
    px = list(thumb.getdata())
    n = len(px)
    lum = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px) / n
    warm = sum(p[0] - p[2] for p in px) / n  # >0 偏暖, <0 偏冷
    sat = sum(max(p) - min(p) for p in px) / n
    sky = rgb_mean(img, (0, 0, w, h // 3))
    ground = rgb_mean(img, (0, 2 * h // 3, w, h))
    fmt = lambda c: f"R{c[0]:.0f}/G{c[1]:.0f}/B{c[2]:.0f}"
    sky_desc = "蓝天" if sky[2] > sky[0] + 15 else ("阴天灰白" if lum > 150 else "深色天空")
    ground_desc = "植被/绿地" if ground[1] > ground[0] and ground[1] > ground[2] else (
        "碎石/沙土" if abs(ground[0] - ground[2]) < 20 else "偏蓝(水面或雪)")
    return (f"亮度 {lum:.0f}/255 | {'偏暖' if warm > 8 else '偏冷' if warm < -8 else '中性'} "
            f"(暖差 {warm:+.0f}) | 饱和度 {sat:.0f}/255\n"
            f"天空区: {fmt(sky)} → {sky_desc}\n"
            f"地面区: {fmt(ground)} → {ground_desc}")


def suggest_id():
    return "scene-" + __import__("time").strftime("%Y%m%d-%H%M%S")


def main():
    commit = None
    if "--commit" in sys.argv:
        commit = sys.argv[sys.argv.index("--commit") + 1]
    if commit:
        imgs = sorted(INBOX.glob("*.jpg")) + sorted(INBOX.glob("*.png")) + sorted(INBOX.glob("*.jpeg"))
        if not imgs:
            print("inbox 为空")
            return
        src = imgs[-1]
        dst = SCENES / commit
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "scene.jpg").unlink(missing_ok=True)
        Image.open(src).convert("RGB").save(dst / "scene.jpg", quality=95)
        img = Image.open(dst / "scene.jpg")
        print(f"已入库 → scenes/{commit}/scene.jpg ({img.size[0]}x{img.size[1]})")
        print(describe(img))
        print(f"\n请让 AI 目检后补写 {dst}/scene.yaml（环境/光线/适配/风险四类标签）")
        src.unlink()
        return
    imgs = sorted(INBOX.glob("*.jpg")) + sorted(INBOX.glob("*.png")) + sorted(INBOX.glob("*.jpeg"))
    if not imgs:
        print("inbox 为空。把场景图丢进 inbox/ 后运行本脚本。")
        return
    for p in imgs:
        img = Image.open(p)
        print(f"=== {p.name} ({img.size[0]}x{img.size[1]}) ===")
        print(describe(img.convert("RGB")))
        print(f"建议场景 id: {suggest_id()}\n")


if __name__ == "__main__":
    main()
