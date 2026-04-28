---
title: 工程知识库
description: 个人工程实践知识库 - 沉淀 Java、MySQL、系统设计、网络与操作系统、设计模式、重构案例和 AI 协作技巧
permalink: /
---

> 个人工程实践知识库，沉淀 Java、MySQL、系统设计、网络与操作系统、设计模式、重构案例与 AI 协作技巧。

## 站点说明

1. 站点由 GitHub Pages + Jekyll cayman 主题渲染。
2. 每个知识域独立目录，目录内的 `索引.md` 或 `README.md` 为主题导航入口。
3. 所有问题节点保持「可枚举、可补充、可维护」。

## 知识体系

### Java

- [Java 知识体系索引](./Java知识体系/索引.md)
  - [并发与多线程](./Java知识体系/并发与多线程.md)
  - [OOP](./Java知识体系/OOP.md)
  - [反射](./Java知识体系/反射.md)
  - [JavaAgent](./Java知识体系/JavaAgent.md)
  - [JDK](./Java知识体系/JDK.md)
  - [JVM](./Java知识体系/JVM.md)
  - [常见问题排查](./Java知识体系/常见问题排查.md)
- [Java 并发与 JUC：线程池](./Java并发与JUC/线程池.md)

### MySQL

- [MySQL 知识体系索引](./MySQL知识体系/索引.md)
  - [主要组成与隔离级别](./MySQL知识体系/主要组成与隔离级别.md)
  - [分区分表](./MySQL知识体系/分区分表.md)
  - [SQL 优化](./MySQL知识体系/SQL优化.md)
  - [日志](./MySQL知识体系/日志.md)
  - [高可用](./MySQL知识体系/高可用.md)
  - [性能优化](./MySQL知识体系/性能优化.md)
  - [索引相关](./MySQL知识体系/索引相关.md)
  - [其他参数优化](./MySQL知识体系/其他参数优化.md)
  - [事务](./MySQL知识体系/事务.md)

### 系统设计

- [系统设计知识体系索引](./系统设计知识体系/索引.md)
  - [核心因素](./系统设计知识体系/核心因素.md)
  - [设计模式](./系统设计知识体系/设计模式.md)
  - [经典题型](./系统设计知识体系/经典题型.md)
  - [常见计算机设计](./系统设计知识体系/常见计算机设计.md)

### 网络与操作系统

- [网络与操作系统索引](./网络与操作系统/README.md)
  - 操作系统：[内核态与用户态](./网络与操作系统/os/内核态与用户态.md) · [协程与线程](./网络与操作系统/os/协程与线程.md) · [DMA](./网络与操作系统/os/DMA.md) · [中断](./网络与操作系统/os/中断.md) · [IO 模型](./网络与操作系统/os/IO模型.md) · [硬件](./网络与操作系统/os/硬件.md) · [信号量](./网络与操作系统/os/信号量.md) · [内核缓冲](./网络与操作系统/os/内核缓冲.md)
  - 网络：[TCP/IP 基础](./网络与操作系统/network/TCP_IP基础.md) · [HTTP 状态码](./网络与操作系统/network/HTTP状态码.md) · [HTTPS](./网络与操作系统/network/HTTPS.md) · [TCP 专题](./网络与操作系统/network/TCP专题.md) · [组网与协议](./网络与操作系统/network/组网与协议.md)

### 数据结构与算法

- [数据结构与算法索引](./数据结构与算法/README.md)
  - 算法：[注意事项](./数据结构与算法/算法/注意事项.md) · [重点 tag](./数据结构与算法/算法/重点tag.md) · [刷题平台](./数据结构与算法/算法/刷题平台.md) · [思想](./数据结构与算法/算法/思想.md)
  - Redis：[数据结构总览](./数据结构与算法/其他场景/redis/数据结构总览.md) · [BloomFilter](./数据结构与算法/其他场景/redis/BloomFilter.md) · [ZSet 与 SkipList](./数据结构与算法/其他场景/redis/ZSet与SkipList.md) · [Geohash](./数据结构与算法/其他场景/redis/Geohash.md)
  - MySQL：[索引结构与 B+Tree](./数据结构与算法/其他场景/mysql/索引结构与BPlusTree.md) · [Hash 索引对比](./数据结构与算法/其他场景/mysql/Hash索引对比.md)
  - JDK：[JUC 核心问题](./数据结构与算法/其他场景/jdk/JUC核心问题.md) · [集合类总览](./数据结构与算法/其他场景/jdk/集合类总览.md)
  - 其他：[Bitmap 使用场景](./数据结构与算法/其他场景/bitmap使用场景.md)

## 模式与重构

### 设计模式落地实践

- [Factory + Handler 模式](./模式落地实践/factory-handler-pattern.md)
- [Adapter + Provider 模式](./模式落地实践/adapter-provider-pattern.md)
- [Builder + Director 模式](./模式落地实践/builder-director-pattern.md)
- [State + Machine / Engine 模式](./模式落地实践/State%20%2B%20Machine或Engine%20模式落地实践.md)
- [Converter / Mapper + Decorator 模式](./模式落地实践/Converter%20或%20Mapper%20%2B%20Decorator%20模式落地实践.md)
- [Publisher + Listener / Observer 模式](./模式落地实践/Publisher%20%2B%20Listener或Observer%20模式落地实践.md)
- [责任链模式](./模式落地实践/责任链模式.md)

### 重构案例

- [CapitalFlowService 重构案例](./重构案例/CapitalFlowService%20重构案例.md)

## AI 协作

- [高效 Prompt 模板](./AI代码审查模板/effective-prompts.md)
- [代码审查模板](./AI代码审查模板/代码审查模板.md)

## 简历与项目

- [resume-projects 索引](./resume-projects/README.md)
  - [账户缓存架构优化项目](./resume-projects/账户缓存架构优化项目.md)
  - [账户缓存优化（简历版本）](./resume-projects/账户缓存优化-简历版本.md)

## 维护规则

1. 新增主题：在对应一级目录新增 `md` 文件，并在该目录的 `索引.md` 或 `README.md` 中追加导航。
2. 新增一级主题：先建立目录与索引文件，再在本 README 的「知识体系」段落追加链接。
3. 文件命名：保持中文目录与中文术语，原始英文术语保留（如 `MVCC`、`Online DDL`、`MRR`）。
4. 文档结构：每个主题文件统一包含「知识点清单 + 待补充项」两段。
5. 链接规范：使用相对路径，含空格或特殊字符的文件名采用 URL 编码。

## 在 Cursor 中使用

### 通过 @ 引用本地知识

```text
@C:\Users\tongyu\Documents\knowledge-base\Java知识体系\并发与多线程.md
请按这份大纲补充 AQS 入队流程。
```

### 通过 GitHub Pages 引用线上链接

```text
请参考 https://youmu1.github.io/knowledge/Java知识体系/JVM.html 的 GC 章节进行回答。
```

## GitHub Pages 配置说明

1. Jekyll 主题：`jekyll-theme-cayman`，配置位于 [`_config.yml`](./_config.yml)。
2. 排除项：`.obsidian/`、`*.base`、`terminals/` 等本地工具产物不参与构建。
3. 启用方式：在 GitHub 仓库 `Settings → Pages` 选择 `Deploy from a branch`，分支选 `main`，目录选 `/ (root)`。

## 更新日志

1. 2026-04-28：重构 README 为 GitHub Pages 首页，新增 `_config.yml`，整合多套知识体系导航。
2. 2026-01-09：创建知识库，添加 Factory+Handler 模式与 CapitalFlowService 重构案例。

Side effects: 仅修改 `README.md` 与新增 `_config.yml`，未删除其它知识文件。
