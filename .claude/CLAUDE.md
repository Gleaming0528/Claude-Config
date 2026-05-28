# .claude/ Configuration

AI agent / skill / rule / command 配置 — HPC 平台四层架构。

完整目录请直接 `ls .claude/{agents,skills,rules,commands}/` 查看（避免文档目录树过期）。
具体清单与触发规则见 [README.md](./README.md)。

## 四层职责

| 层 | 路径 | 角色 | 加载方式 |
|----|------|------|----------|
| Rules | `rules/` | 编码约束 | 按 glob 自动生效 |
| Skills | `skills/` | 方法论 + 工作流 | 按关键词按需加载 |
| Agents | `agents/` | 子代理执行 | Task 工具派遣 |
| Commands | `commands/` | 高频操作入口 | `/cmd` 触发 |

层间原则：Rule 管约束、Skill 管流程、Agent 管执行、Command 管入口；互相引用但不重复。

## 维护铁律

- **不要在本文件复制目录树或文件清单** — 一旦写下就会过期（Bug 案例：曾列 17 个 skills，实际 33 个）。
  - 真理来源：磁盘目录本身 + `README.md` 的详细表格
  - 本文件只放「层级关系」「设计原则」这种几乎不变的内容
- 新增 / 删除 rule、skill、agent、command 时，只需同步更新 `README.md` 表格。
