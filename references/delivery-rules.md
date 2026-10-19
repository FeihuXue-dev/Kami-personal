# Kami 交付规则（本地强制）

本文件汇总作者在**用 Kami 制作交付物**时额外遵守的本地规则。它们来自本机项目级 `AGENTS.md`，与 `SKILL.md` 的关系是：`SKILL.md` 负责方法与流水线，本文件负责不可跳过的交付约束；两者重复时按更严格的一条执行。

适用范围：任何经 Kami 产出的 PDF、HTML 页面、幻灯片、报告与作品集。单页模板（resume / letter / one-pager）同样适用，但可跳过目录与书签要求。

## 1. 同内容文档同步（强制）

- 修改文档内容前，必须识别该文档的同内容源文件、发布文件和派生产物；常见组合包括 Markdown、HTML、PDF、图片预览页及内容 JSON。
- 修改任一内容源后，必须在同一任务中同步更新所有同内容文件；PDF、HTML 和预览图应由更新后的源文件重新生成，不得保留内容过期的副本。
- 交付前必须核对各格式的标题、章节与新增/删除内容一致，并执行相应的构建或渲染校验；若因环境限制无法同步，必须明确说明未同步的文件及原因，不能默认忽略。

## 2. PDF 构建（强制）

- 任何 PDF 一律走本地 Kami 技能（安装路径 `~/.agents/skills/kami`）的模板与流水线产出，禁止用 Chrome headless、cupsfilter、pandoc 或裸调 weasyprint 等临时方案代替。
- 套模板填充，不改模板 CSS；含代码用 Shiki（`scripts/rebuild_shiki_pdf.py`）、含公式用 MathJax（`scripts/math_render.py`），不得交付单色代码块或原始 TeX。
- 交付前跑 Kami 校验：`--check-content`、`--check-style`、`--check-placeholders`、`--check-markdown`、`--check-density`、`--check-fonts`、`--check-visual`，并用 `scripts/add_outline.py` 保留或补齐 PDF 书签。
- 打码标记不得使用星号：Kami 的 markdown 残留检查会把 `**` 判为未转换的粗体标记，因此统一用 `[已打码]`。
- 含代码或公式时，构建前先运行 `scripts/ensure_shiki.sh` / `scripts/ensure_mathjax.sh`；依赖缺失即视为构建失败，不得降级交付。

## 3. 公式不得截断（强制）

- 交付 PDF 中任何数学公式必须完整可见：不得被裁掉左右两端、不得压住页边、不得越过正文文本栏。渲染器对超宽公式不会自动换行也不会缩放，结果是静默截断（读者只看到半个等式，且没有任何报错），因此必须当作发布门禁而非观感问题。
- 构建后必须运行公式适配门禁：`python3 scripts/check_formula_fit.py <交付.pdf>`。该脚本从 PDF 自身几何推导正文文本栏，逐页比对全部矢量墨迹范围；只要有一页的墨迹越过文本栏即视为构建失败。
- 超宽公式一律换行拆分，而不是缩小绕过：并排多项改写成 `\begin{aligned}` 多行；把常量、约束条件移入逐符号图例；或把长行内公式改成短式或独立成行。禁止靠调小字号、压缩图片、减小页边距来挤出宽度。
- 拆分重点排查对象：并排的多个等式（`\qquad` 串联）、`cases` 分段函数、矩阵与块对角、长下标链（如 `logits^{l-1}`）、含 `\mathbb{E}` 期望与 `\operatorname*{arg\,min}` 的目标函数、以及行内长公式紧跟在中文全角括号后的情形（全角括号禁止断行，会把公式整体顶出栏外）。
- 交付前必须目视核对每条公式的左右边界完整性，并在完成报告里给出该门禁的运行结果；未跑或未通过不得声明交付完成。
- 每一条显示公式还必须带逐符号图例并通过 `python3 scripts/check_symbols.py --check <源 HTML>`；规则细节见 `references/writing.md` §9 与 `SKILL.md` 的公式符号 gate。

## 4. PDF 解释概念（强制）

- 用 PDF 解释任何概念时，必须完整解释该概念的来源。
- 展示数学公式时，必须详细讲解该公式的来源，不可以跳跃步骤。
- 执行口径：来源至少交代提出者/出处（论文、教材、官方文档）、要解决的问题、关键假设与符号定义；推导按步骤展开，每一步说明依据的代数变形、假设或定义，不能只给结论。

## 5. 深度学习 / 机器学习 / 计算机视觉 / 大模型 网络解释

- 介绍网络架构或特征时，必须从网络上检索可靠的、对应的网络架构图片，且**不可以生成网络架构图片**。
- 优先使用原始论文、官方文档或厂商/标准材料中的图，并在图注中标注来源与图号/表号；检索不到时在材料缺口表中标明并询问一次，不得用相似图、重绘图或生成图顶替。
- 手绘 SVG 或图像生成只用于通用示意（自创流程、数据图表、抽象比喻）或用户明确要求重绘的场景。

## 6. 交付前检查清单

| 检查 | 命令 / 动作 |
|---|---|
| 模板与流水线 | 确认产物由 Kami 模板生成，未换用 headless 浏览器、pandoc、cupsfilter 或裸 weasyprint |
| 同内容同步 | 逐项核对 Markdown / HTML / PDF / 预览图 / JSON 的标题与章节一致 |
| 代码高亮 | `bash scripts/ensure_shiki.sh`，交付 HTML 中存在静态 `shiki-rendered` |
| 数学渲染 | `bash scripts/ensure_mathjax.sh`、`python3 scripts/math_render.py --check <html>` |
| 符号图例 | `python3 scripts/check_symbols.py --check <源 HTML>` |
| 公式不越栏 | `python3 scripts/check_formula_fit.py <交付.pdf>` |
| 书签/目录 | `python3 scripts/add_outline.py <html> <pdf>`；≥6 页检查可见目录页 |
| 结构/字体/视觉 | `--check-content`、`--check-style`、`--check-placeholders`、`--check-markdown`、`--check-density`、`--check-fonts`、`--check-visual` |
| 打码 | 仅使用 `[已打码]`，不出现星号掩码 |
| 概念与公式讲解 | 概念来源完整；公式逐步推导，无跳步 |
| 架构图 | 取自可引用原始来源，标注出处；无生成图 |

## 7. 规则来源

- 本机全局与项目级 `AGENTS.md`：同内容文档同步、PDF 构建、公式不得截断、概念解释、网络架构图。
- 本文件只收录与 Kami 交付直接相关的条款；密钥安全、浏览器后台运行、模型选用与多角色编排等与本技能无关的规则不在此重复。
- 本机规则更新时，同步更新本文件，并保持 `SKILL.md` 的对应门禁一致。
