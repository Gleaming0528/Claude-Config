---
name: ui-design-brain
description: 基于 60+ 组件最佳实践生成生产级 UI。适用于设计页面、UI 设计、组件设计、表单设计、dashboard 设计、导航设计。
---

# UI Design Brain

This skill provides a curated knowledge base of 60+ UI component patterns sourced from [component.gallery](https://component.gallery) and enriched with best practices, layout guidance, and usage rules. It replaces generic guessing with real design-system knowledge when generating interfaces.

**Before writing any UI code**, consult this skill to select the right components and follow their best practices. Read [components.md](components.md) for the full reference.

## When to Use This Skill

Apply whenever the user asks to build, design, or generate:
- Web pages, landing pages, marketing sites
- SaaS dashboards, admin panels, settings pages
- Forms, data tables, navigation structures
- Modals, drawers, popovers, or overlay patterns
- Any React, HTML/CSS, or Tailwind UI component

## Design Philosophy

Every generated interface should feel **modern, minimal, and production-ready** — not like a template.

### Core Principles

1. **Restraint over decoration.** Fewer elements, highly refined. White space is a feature.
2. **Typography carries hierarchy.** Pair a distinctive display font with a clean body font. Maximize weight contrast between headings and labels.
3. **One strong color moment.** Neutral palette first (warm off-whites, near-blacks, muted mid-tones). Introduce one confident accent. If it could appear on a poster or book cover, it's probably timeless.
4. **Spacing is structure.** Use an 8 px grid. Tighter gaps group related elements; generous gaps let hero content breathe.
5. **Accessibility is non-negotiable.** WCAG AA contrast minimums. Focus indicators. Semantic HTML. Keyboard navigation.
6. **No generic AI aesthetics.** Avoid: purple-on-white gradients, Inter/Roboto defaults, evenly-spaced card grids, and cookie-cutter layouts. Every interface should feel designed for its specific context.

### Quality Bar

The output should match what you'd expect from a senior product designer at a top SaaS company:
- Clean visual rhythm with intentional asymmetry
- Obvious interactive affordances (hover, focus, active states)
- Graceful edge cases (empty states, loading, error)
- Responsive without breakpoint artifacts

## Workflow

### Step 1 — Identify Components

Read the user's request and determine which UI components are needed. Reference [components.md](components.md) to find each component by name or alias.

Common mappings:
- "navigation" → Header, Navigation, Breadcrumbs, Tabs
- "form" → Form, Text input, Select, Checkbox, Radio button, Button
- "data display" → Table, Card, List, Badge, Avatar
- "feedback" → Alert, Toast, Modal, Spinner, Progress bar, Empty state
- "input" → Text input, Textarea, Select, Combobox, Datepicker, File upload, Slider
- "overlay" → Modal, Drawer, Popover, Tooltip, Dropdown menu

### Step 2 — Apply Best Practices

For each component in the interface, follow its best practices from the reference. Key rules that apply broadly:

**Layout**
- Single-column forms — faster to scan
- Consistent vertical lanes in repeated rows (lists, tables)
- Fixed-width slots for icons and actions, even when empty
- Cards: media → title → meta → action hierarchy

**Interaction**
- Buttons: verb-first labels ("Save changes", not "Submit"), one primary per section
- Modals: always provide X, Cancel, and Escape; trap focus; return focus on close
- Toasts: auto-dismiss 4–6 s, allow manual dismiss, stack newest on top
- Toggles: immediate effect only — use checkboxes in forms that require Save

**Typography & Spacing**
- Strict heading hierarchy (h1 → h2 → h3), one h1 per page
- Minimum 44 px touch targets on mobile
- Labels above inputs (vertical forms) or beside (horizontal)
- Placeholder text as format hint, never as label replacement

**States**
- Empty states: illustration + helpful headline + primary CTA
- Loading: skeleton screens > spinners (show after 300 ms delay)
- Validation: inline on blur, not on every keystroke
- Disabled elements: visually distinct but still readable

### Step 3 — Choose a Design Direction

Select the style preset that best matches the user's intent, or ask if unclear:

**Modern SaaS** (default)
- Neutral palette, one strong accent
- 8 px grid, generous white space
- Clean, professional, spacious

**Apple-level Minimal**
- Near-monochrome, warm grays
- Large type hierarchy, tight tracking on display text
- Abundant white space, micro-interactions (150–250 ms ease-out)

**Enterprise / Corporate**
- Information-dense, well-defined regions
- Compact spacing scale (4/8/12/16/24 px)
- Robust form handling, fully keyboard-navigable

**Creative / Portfolio**
- Bold, expressive, strong visual personality
- Asymmetric layouts, dramatic scale contrast
- Editorial typography, vivid accent colors

**Data Dashboard**
- Data-dense, optimised for scannability
- Consistent vertical alignment across rows
- Clear metric hierarchy: KPI → trend → detail

### Step 4 — Generate Code

Write production-ready code following these rules:

```
Stack:       React + Tailwind CSS (unless user specifies otherwise)
Spacing:     Tailwind spacing scale (p-2, gap-4, etc.) on an 8px grid
Colors:      CSS variables or Tailwind config for palette consistency
Typography:  Tailwind text utilities; expressive font pairings via Google Fonts
States:      Implement hover, focus, active, disabled for all interactive elements
Responsive:  Mobile-first; test at 375, 768, 1440 px
Accessibility: Semantic HTML, ARIA where needed, focus management
```

## Component Quick Reference

Below are the 15 most commonly needed components. For the full 60+ component reference with best practices, aliases, and layout examples, see [components.md](components.md).

| Component | When to use | Key rule |
|-----------|------------|----------|
| **Button** | Trigger actions | Verb-first labels; one primary per section |
| **Card** | Represent an entity | Media → title → meta → action; shadow OR border, not both |
| **Modal** | Focused attention | Trap focus; X + Cancel + Escape to close |
| **Navigation** | Page/section links | 5–7 items max; clear active state |
| **Table** | Structured data | Sticky header; right-align numbers; sortable columns |
| **Tabs** | Switch panels | 2–7 tabs; active indicator; accordion on mobile |
| **Form** | Collect input | Single column; labels above; inline validation on blur |
| **Toast** | Brief confirmation | Auto-dismiss 4–6 s; undo action for destructive ops |
| **Alert** | Important status | Semantic colors + icon; max 2 sentences |
| **Drawer** | Secondary panel | Right for detail, left for nav; 320–480 px desktop |
| **Search input** | Find content | Cmd/Ctrl+K shortcut; debounce 200–300 ms |
| **Empty state** | No data | Illustration + headline + CTA; positive framing |
| **Skeleton** | Loading placeholder | Match actual layout shape; shimmer animation |
| **Badge** | Status/metadata label | 1–2 words; pill shape for status; limited color palette |
| **Dropdown menu** | Action/nav options | 7±2 items; destructive actions last in red |

## Anti AI-slop 规则

AI slop = AI 训练语料里最常见的「视觉最大公约数」。用了它们，产品看起来就像「又一个 AI 做的页面」，品牌辨识度归零。

**反 slop 的逻辑**：用户要的是他的产品被认出来 → AI 默认产出 = 所有品牌混合 = 没有品牌被认出来 → 反 slop 不是审美洁癖，是保护品牌识别度。

### 必须规避的 slop（带正向替代）

| slop 元素 | 为什么是 slop | 正向替代 | 何时可破例 |
|-----------|-------------|---------|-----------|
| 紫色渐变背景 | AI 语料里「科技感」的万能公式 | 品牌色 / `oklch()` 定义的和谐色 | 品牌本身用紫渐变（如 Linear） |
| Emoji 当图标 | 「不够专业就用 emoji 凑」的惯性 | 真正的 icon 系统（Lucide/Heroicons）或不用 | 品牌本身用（如 Notion）、儿童/轻松场景 |
| 圆角卡片 + 左彩色 border accent | 2020-2024 Tailwind 时期的烂大街组合 | 诚实的边界/分隔，用 spacing 和层级代替 | 用户明确要求 |
| SVG 手画人物/场景 | AI 画的 SVG 人脸永远五官错位 | 真实素材、高质量插图库、或诚实 placeholder | 几乎没有 |
| Inter/Roboto/系统字体做标题 | 太普通，看不出「有设计过」 | display + body 字体配对（见品位锚点） | 品牌 spec 明确用这些字体 |
| 赛博霓虹 / `#0D1117` 深蓝底 | GitHub dark mode 美学的烂大街复制 | 有温度的底色（暖灰/米白/品牌深色） | 开发者工具产品且品牌本身走这方向 |
| 装饰性 icon 每处都配 | 每个标题配 icon = 视觉噪音 | icon 只在承载差异化信息时使用 | 产品核心卖点需要信息密度支撑 |
| 编造 stats/quotes 填空间 | 假数据不如空白 | 留白，或要求提供真内容 | — |
| 散落的微交互动画 | 到处 bounce/fade 反而分散注意力 | 一次精心编排的 page load 动画 | — |

### 正向品味信号

- `text-wrap: pretty` + CSS Grid — 排版细节是 AI 分不清的「品味税」
- `oklch()` 色彩空间 — 感知均匀，自动生成和谐色阶
- 一个细节做到 120%，其他做到 80% — 品味 = 在合适的地方足够精致，不是均匀用力
- 中文用「」引号不用 "" — 排印规范的细节信号
- 留白是设计手段，不是偷懒 — 空白用构图解决，不靠编造内容填满

### 判断边界

「品牌本身用」是唯一能合法破例的理由。品牌 spec 里明写了用紫渐变，那就用 — 此时它不再是 slop，是品牌签名。

## 品位锚点

当没有明确 design system 时，默认往这些方向走：

| 维度 | 首选 | 避免 |
|------|------|------|
| **字体** | 衬线 display（Newsreader/Source Serif/EB Garamond）+ `-apple-system` body | 全场 Inter 或系统默认字体 — 没风格 |
| **色彩** | 一个有温度的底色 + **单个** accent 贯穿全场 | 多色聚类（除非数据真有 ≥3 分类维度） |
| **信息密度（克制型，默认）** | 少一层容器、少一个 border、少一个装饰 icon — 给内容留气口 | 每条卡片都配无意义 icon + tag + status dot |
| **信息密度（高密度型）** | 当产品核心是数据/AI/监控（Dashboard、Tracker），每屏至少 3 处差异化信息 | 只放一个按钮一个图表 — 没表达产品智能感 |
| **细节签名** | 留一处「值得截图」的质感：极淡纹理 / serif 斜体引语 / 精致的空状态插图 | 到处平均用力，结果处处平淡 |

**两条原则同时生效**：
1. 品味 = 一个细节做到 120%，其它做到 80%
2. 减法是 fallback 不是普适律 — 产品需要信息密度时，加法优先于克制

## 设计方向坐标系

需求模糊时（「做个好看的」「帮我设计」），用这个坐标系选方向，比「好看」「简洁」精确 10 倍：

| 流派 | 气质 | 代表设计师/公司 | 核心特征 | 适合场景 |
|------|------|---------------|---------|---------|
| **信息建筑派** | 理性、数据驱动、克制 | Pentagram、iA Writer、Fathom | 字体即语言，网格即思想，每个像素承载信息 | Dashboard、数据产品、专业工具 |
| **运动诗学派** | 动感、沉浸、技术美学 | Locomotive、Active Theory | 滚动叙事、视差深度、电影化分镜 | Landing page、产品发布、品牌展示 |
| **极简主义派** | 秩序、留白、精致 | Müller-Brockmann、Build | 数学精确的网格、奢侈品级留白、微妙字重对比 | 高端品牌、设置页、文档 |
| **实验先锋派** | 先锋、视觉冲击 | Zach Lieberman、Ash Thorp | 生成艺术、算法图形、电影级光影 | 创意展示、技术 Demo、概念验证 |
| **东方哲学派** | 温润、诗意、思辨 | Takram、Kenya Hara | 柔和科技感、极致留白、设计即清空 | 内容产品、阅读体验、品牌差异化 |

**使用方法**：从不同流派各挑一个方向，生成 2-3 个视觉 demo 让用户选，再深化。禁止从同一流派推荐 2 个以上 — 差异化不够用户看不出区别。

**HPC 平台推荐**：数据密集型页面（任务列表、节点监控、队列管理）→ 信息建筑派；Landing page / 文档站 → 极简主义派或东方哲学派。

## UI Anti-Patterns

通用 UI 反模式（与 AI slop 无关的工程质量问题）：

- **Rainbow badges** — 每个状态一个亮色但无语义含义
- **Modal inside modal** — 复杂流程用页面或 Drawer
- **Disabled submit with no explanation** — 必须提示缺什么
- **Spinner for predictable layouts** — 用 skeleton 代替
- **"Click here" links** — 链接文本必须描述目的地
- **Hamburger menu on desktop** — 桌面端用可见导航
- **Auto-advancing carousels** — 让用户控制翻页
- **Placeholder-only form fields** — 必须用可见 label
- **Equal-weight buttons** — 建立 primary/secondary/tertiary 层级
- **Tiny text (< 12 px)** — body 最小 14 px，推荐 16 px
