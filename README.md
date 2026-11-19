# scene-library — 婚纱套图场景图素材库

lvpai-wedding-sets skill 的场景资产库。**大图只存 GitHub，本地零常驻；用 `fetch_ref.py` 按需拉取**（2026-11-11 起，见 `references/19-素材库引用规则.md`「取图纪律」）。

## 内容

- `index.yaml` — 全库索引：场景 id / 原图外部路径 / 尺寸 / 色调 / 季节提示（本地）
- `thumbs/<场景id>.jpg` — 512px 目检缩略图（本地；2026-11-11 由 GitHub scene.jpg 补建）
- `matching-rules.md` — 场景×妆造×机位匹配规则（生图前必读，本地）
- `scenes/<地点>/<场景id>.jpg` — 默认 2048px 压缩参考图（q90，**只在 GitHub**，按需拉取）；库尔德宁自 2026-11-19 起存原生 4K、无损 PNG
- `build_index.py` — 从外部原图目录重建索引（PIL）
- `scene_tag.py` — inbox 单图打标工具

## 取图（生图喂参考）

```bash
# 目检缩略图（本地直接看）
thumbs/<场景id>.jpg
# 拉大图喂 gen.py -i（输出缓存路径）
python ../scripts/fetch_ref.py --lib scene --id <场景id>
```

## 维护流程

1. 新场景图放进本机素材目录（如有新原图时）
2. `python build_index.py --root <素材目录> --repo` 全量重建（含缩略图）
3. 人工/WorkBuddy 目检缩略图，补 scene.yaml 标签
4. push 到 GitHub（需临时 `git clone --depth 1` 或在任一保留 .git 的机器上操作；本地常规使用无需 git）

## 权限

- 公开仓库：无需凭据即可拉取；如遇限流可用 gh CLI 登录或 `GH_TOKEN` 提高配额
- 售卖交付：打 zip/git bundle 随 skill 包交付，不开放仓库权限
