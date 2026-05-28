---
description: Security guidelines — cross-language security principles and response protocol
alwaysApply: true
---

# Security Guidelines

## 提交前必检

- [ ] 无硬编码密钥（API key、password、token）
- [ ] 所有用户输入已校验
- [ ] 错误消息不泄露敏感数据
- [ ] 认证/授权已验证

语言特定安全规则：Go 见 `go-security.md`，前端见 `react-frontend.md`。

## Security Response Protocol

发现安全问题时：
1. **立即停止**当前工作
2. 用 **code-reviewer** agent 检查（自动包含安全项）
3. CRITICAL 问题必须修复后才能继续
4. 轮换已暴露的密钥
5. 排查代码库中类似问题
