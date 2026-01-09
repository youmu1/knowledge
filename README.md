# 工程知识库

> 个人工程实践知识库，用于沉淀设计模式、重构案例、业务规则和 AI 协作技巧。

## 📖 简介

这是一个**本地知识库**，独立于具体项目，用于记录和积累在软件开发过程中的学习成果和最佳实践。

## 🗂️ 目录结构

```
knowledge-base/
├── patterns/              # 设计模式落地实践
│   └── factory-handler-pattern.md
├── refactoring/          # 重构案例记录
│   └── 2026-01-09-capital-flow-refactoring.md
├── business-rules/       # 核心业务逻辑定义
├── ai-collaboration/    # AI 协作技巧
│   ├── effective-prompts.md
│   └── code-review-templates.md
├── INDEX.md             # 知识库索引
└── README.md           # 本文件
```

## 🚀 快速开始

### 1. 查看索引
打开 [INDEX.md](./INDEX.md) 查看所有知识条目。

### 2. 查找知识
- **按模式查找**：查看 `patterns/` 目录
- **按案例查找**：查看 `refactoring/` 目录
- **按技巧查找**：查看 `ai-collaboration/` 目录

### 3. 添加新知识
1. 选择合适的分类目录
2. 创建 Markdown 文件
3. 更新 `INDEX.md` 添加索引

## 💻 在 Cursor 中使用

### 方法一：使用 @ 符号引用
```
@C:\Users\tongyu\Documents\knowledge-base\patterns\factory-handler-pattern.md
请参考这个模式来优化代码
```

### 方法二：在 .cursorrules 中引用
在项目根目录的 `.cursorrules` 文件中：
```markdown
@import C:\Users\tongyu\Documents\knowledge-base\patterns\factory-handler-pattern.md
```

## 📝 使用场景

### 场景 1：开始新任务
```
@C:\Users\tongyu\Documents\knowledge-base\patterns\factory-handler-pattern.md
请参考这个模式来实现订单处理功能
```

### 场景 2：代码审查
```
@C:\Users\tongyu\Documents\knowledge-base\ai-collaboration\code-review-templates.md
请按照模板审查这段代码
```

### 场景 3：重构代码
```
@C:\Users\tongyu\Documents\knowledge-base\refactoring\2026-01-09-capital-flow-refactoring.md
参考这个案例，重构当前代码
```

### 场景 4：生成文档
```
@C:\Users\tongyu\Documents\knowledge-base\ai-collaboration\effective-prompts.md
使用"总结重构要点"模板，生成本次重构的文档
```

## 🔄 工作流程

### 学习新知识
1. **实践** → 在项目中应用设计模式或重构代码
2. **总结** → 让 AI 生成学习总结
3. **沉淀** → 存入知识库对应目录
4. **索引** → 更新 INDEX.md

### 应用已有知识
1. **查找** → 在 INDEX.md 或目录中查找相关模式
2. **引用** → 在 Cursor 中使用 @ 符号引用
3. **应用** → 让 AI 参考模式实现代码
4. **验证** → 检查是否符合最佳实践

## 📚 知识分类

### 设计模式 (patterns/)
记录设计模式在企业级 Java 开发中的落地实践，包括：
- 模式概述
- 核心组件
- 解决的问题
- 使用场景
- 工程实践要点

### 重构案例 (refactoring/)
记录具体的重构案例，包括：
- 重构背景
- 重构前代码
- 重构方案
- 重构成果
- 关键学习点

### 业务规则 (business-rules/)
记录核心业务逻辑的显式定义，包括：
- 业务规则描述
- 边界条件
- 异常情况处理

### AI 协作 (ai-collaboration/)
记录与 AI 协作的高效技巧，包括：
- Prompt 模板
- 代码审查模板
- 最佳实践

## 🔍 维护建议

### 定期更新
- 每次完成重要重构后，立即总结并存入知识库
- 每月回顾一次，整理和优化已有知识

### 版本控制
建议为知识库创建 Git 仓库：
```bash
cd C:\Users\tongyu\Documents\knowledge-base
git init
git add .
git commit -m "Initial knowledge base"
```

### 知识质量
- 每个知识条目应该包含：问题、方案、代码示例、收益分析
- 保持文档的时效性，及时更新过时的内容

## 📖 相关资源

- [设计模式 - 策略模式](https://refactoring.guru/design-patterns/strategy)
- [Spring Framework 文档](https://spring.io/projects/spring-framework)
- [Effective Java](https://www.oracle.com/java/technologies/effective-java.html)

## 📅 更新日志

- **2026-01-09**: 创建知识库，添加 Factory+Handler 模式和 CapitalFlowService 重构案例

---

**提示**: 这个知识库是活的，会随着你的学习和实践不断成长。保持记录，保持学习！

