# Kami · personal

个人维护的 [Kami](https://github.com/tw93/Kami) 排版 skill。仓库根目录就是 skill 根目录，可直接安装到 `~/.agents/skills/kami`。

- 上游基线：`tw93/Kami` 标签 `V1.13.0`（上游 skill 位于 `plugins/kami/skills/kami`）
- 本仓库版本：`1.13.1`
- 许可：MIT（原始版权归 Tw93，见 `LICENSE`）

## 相对上游的改动

一句话：把「代码高亮、数学公式、PDF 结构、图表来源」从可选建议改成可机械校验的发布门禁。

| 主题 | 上游 V1.13.0 | 本仓库 |
|---|---|---|
| 代码高亮 | 可选 Pygments，五色 token，缺失时静默单色 | 强制 Shiki（Zed One Light），静态 `shiki-rendered`，缺 Shiki 即构建失败 |
| 数学公式 | 无 | 强制 LaTeX（`\(...\)` / `\[...\]`）→ 自包含 MathJax SVG |
| 公式可读性 | 无 | 每条显示公式必须带逐符号图例 `.sym-list`，`check_symbols.py` 门禁 |
| 公式排版 | 无 | `check_formula_fit.py` 用 PDF 几何检查墨迹是否越出正文栏 |
| PDF 导航 | 依赖渲染器 | `add_outline.py` 保留/回填书签；≥6 页长文要求可见目录页 |
| 图表来源 | 允许手绘/生成 | 既有架构、模型、设备、标准图必须取自原始文献，禁止重画或生成 |
| PDF 封面 | 文本封面 | 接入 `mono-color` 技能生成单/双色封面（文本仍由 HTML 叠加） |
| 写作规范 | 无逐符号要求 | `writing.md` §9「公式逐符号可解码」及发布检查项 |

### 新增文件

| 文件 | 作用 |
|---|---|
| `scripts/ensure_shiki.sh` | 在 `~/.cache/kami/shiki` 安装/校验 Shiki 4.4.3 |
| `scripts/shiki_highlight.mjs` | Node 侧 Shiki 渲染器 |
| `scripts/rebuild_shiki_pdf.py` | 从源码 HTML 生成独立 Shiki HTML/PDF；检测 PDF 批注，避免覆盖已审阅文件 |
| `scripts/ensure_mathjax.sh` | 在 `~/.cache/kami/mathjax` 安装/校验 MathJax 3 |
| `scripts/math_render.py` | LaTeX/占位符 → MathJax SVG；`--check` 拦截未渲染公式 |
| `scripts/mathjax_svg.js` | MathJax Node 渲染器 |
| `scripts/check_symbols.py` | 逐符号图例门禁 |
| `scripts/check_formula_fit.py` | 公式越栏门禁 |
| `scripts/add_outline.py` | PDF 书签保留/回填 |

### 修改文件

- `SKILL.md`：Shiki/LaTeX/符号/书签/公式越栏门禁；图表溯源规则；mono-color 封面步骤。
- `CHEATSHEET.md`：同步上述门禁的速查条目。
- `references/design.md`：`.sym-list` 规范；语法高亮改为 Zed One Light。
- `references/writing.md`：§9 公式逐符号可解码。
- `references/production.md`：Strict LaTeX mathematics 流程。
- `assets/templates/long-doc{,-en,-ko}.html`：`.formula-unit` / `.sym-list` 样式。
- `scripts/highlight.py`：Pygments → Shiki。
- `scripts/optional_deps.py`：新增 `require_shiki()`。
- `scripts/render.py`：PDF 管线先渲染数学，再高亮代码。
- `scripts/visual.py`：视觉检查页数上限 200 → 300。
- `scripts/package-skill.sh`：打包清单纳入新增脚本。
- `scripts/tests/test_build.py`：Shiki 与数学渲染测试。
- `scripts/check-update.sh`：更新检查指向本仓库。
- `VERSION`：`1.13.0` → `1.13.1`。

## 安装

```bash
# 方式一：直接 clone（会替换现有安装，先备份）
mv ~/.agents/skills/kami ~/.agents/skills/kami.bak
git clone git@github.com:FeihuXue-dev/Kami-personal.git ~/.agents/skills/kami

# 方式二：skills CLI
npx skills add FeihuXue-dev/Kami-personal -a universal -g -y
```

## 依赖

- Python 3.10+：`weasyprint`、`pypdf`、`pymupdf`
- Node.js + npm：Shiki、MathJax（缓存在 `~/.cache/kami`）
- 字体：按上游 `scripts/ensure-fonts.sh` 准备

首次使用先初始化本地渲染依赖：

```bash
bash scripts/ensure_shiki.sh
bash scripts/ensure_mathjax.sh
python3 scripts/build.py --doctor
```

## 校验

```bash
python3 -m py_compile scripts/*.py scripts/tests/*.py
python3 scripts/tests/test_build.py
bash scripts/package-skill.sh /tmp/kami.zip   # 仓库需为 git checkout
```

文档级门禁见 `SKILL.md` Step 5；数学交付物至少应通过：

```bash
python3 scripts/math_render.py --check filled.html
python3 scripts/check_symbols.py --check filled-source.html
python3 scripts/check_formula_fit.py filled.pdf
python3 scripts/add_outline.py filled.html out.pdf
```

## 与上游同步

本仓库是 fork 而非镜像，目录结构（skill 在根目录）与上游 monorepo 不同，不能直接 merge。同步方式：

```bash
git remote add upstream https://github.com/tw93/Kami.git
git fetch upstream --tags
# 手工比对 upstream/plugins/kami/skills/kami 与本地文件
```

`scripts/check-update.sh` 已改为检查本仓库的 Release，不再提示上游更新。

## 已知边界

- 仅跟进到上游 `V1.13.0`；上游 `1.15+` 重写了数学渲染路径，升级时不要整目录覆盖。
- 新增门禁是独立 CLI，未接入 `build.py --verify`；按 `SKILL.md` 的 Step 5 顺序显式运行。
- Shiki/MathJax 需要 Node 与 npm；离线环境需预热 `~/.cache/kami`。
- `check_formula_fit.py` 依赖 PyMuPDF，只检查矢量墨迹范围，不替代人工目视。
