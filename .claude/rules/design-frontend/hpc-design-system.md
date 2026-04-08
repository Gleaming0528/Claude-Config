---
description: HPC 超算平台设计系统 - 基于 Ant Design 的设计令牌和组件规范
globs: ["hpc-ui/**/*.{tsx,ts,css}"]
alwaysApply: false
category: frontend
tags: [design-system, tokens, hpc]
---

# HPC 超算平台设计系统

项目使用 Ant Design 6 + 自定义设计令牌，所有视觉决策必须基于以下令牌体系。

## 设计令牌文件

唯一真相源：`hpc-ui/src/theme/unified-theme.ts`

## 颜色令牌

| 令牌 | 值 | 语义 |
|------|-----|------|
| `colors.primary` | `#667eea` | 品牌主色 |
| `colors.primaryLight` | `#818cf8` | 主色浅变体（hover） |
| `colors.primaryDark` | `#5a6fd8` | 主色深变体（active） |
| `colors.success` | `#52c41a` | 成功/运行中 |
| `colors.warning` | `#faad14` | 警告/等待中 |
| `colors.error` | `#ff4d4f` | 错误/失败 |
| `colors.info` | `#1890ff` | 信息/处理中 |

### 中性色阶

| 令牌 | 值 | 用途 |
|------|-----|------|
| `neutral.gray1` | `#fafafa` | 表头背景 |
| `neutral.gray2` | `#f5f5f5` | 页面背景 |
| `neutral.gray5` | `#bfbfbf` | 禁用/占位 |
| `neutral.gray6` | `#8c8c8c` | 辅助文字 |
| `neutral.gray7` | `#595959` | 次级文字 |
| `neutral.gray8` | `#262626` | 标题文字 |

### 状态颜色映射

资源状态使用 `getStatusColor(status)` 统一映射，不要在组件内硬编码颜色。

## 间距令牌

使用 `spacing` 对象，单位 px：

| 令牌 | 值 | 用途 |
|------|-----|------|
| `xs` | 4 | 紧凑间距 |
| `sm` | 8 | 元素内间距 |
| `md` | 12 | 表单项间距 |
| `base` | 16 | 默认间距 |
| `lg` | 20 | 区块间距 |
| `xl` | 24 | 卡片内边距 |
| `xxl` | 32 | 大区块间距 |

**禁止** 使用 `padding: 17px` 等非令牌值。

## 圆角令牌

| 令牌 | 值 | 用途 |
|------|-----|------|
| `radius.sm` | 4 | Tag、小元素 |
| `radius.md` | 6 | 输入框、按钮 |
| `radius.lg` | 8 | 默认组件 |
| `radius.xl` | 12 | 卡片 |
| `radius.xxl` | 16 | 大容器 |

## 阴影令牌

| 令牌 | 值 | 用途 |
|------|-----|------|
| `shadows.sm` | `0 1px 2px...` | 微弱立体 |
| `shadows.base` | `0 2px 8px...` | 卡片默认 |
| `shadows.md` | `0 4px 12px...` | 悬浮卡片 |
| `shadows.lg` | `0 8px 24px...` | 弹窗/Drawer |

## 响应式断点

| 断点 | 值 | 设备 |
|------|-----|------|
| `sm` | 576px | 手机 |
| `md` | 768px | 平板竖屏（isMobile 分界） |
| `lg` | 1024px | 平板横屏（isTablet 分界） |
| `xl` | 1200px | 标准笔记本 |
| `xxl` | 1600px | 大屏 |

## 通用组件使用规范

### 按钮语义

使用 `<Button semantic="...">` 而非原生 `type`：
- `execute`: 主操作（创建、提交）
- `secondary`: 次要操作（取消、关闭）
- `danger`: 危险操作（删除）

### 空状态

使用 `<EmptyState type="no-xxx">` 而非 `<Empty />`，预设类型包括：
`no-devspaces`, `no-jobs`, `no-datasets`, `no-models`, `no-images`, `no-volumes`, `no-results`

### 确认对话框

危险操作使用 `showDeleteConfirm()` 而非 `Modal.confirm()`。

### 错误展示

使用 `<SmartError>` 组件统一错误展示，支持重试和技术详情。

### 复制文本

使用 `<CopyableText>` 组件，不要手动实现 `navigator.clipboard`。
