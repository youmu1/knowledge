# Redis - ZSet 与 SkipList

## 定义

ZSet（有序集合）是 Redis 中按 score 排序的数据结构，底层实现涉及跳表（SkipList）与哈希结构。

## 原理

1. 通过哈希结构支持成员快速定位。
2. 通过 SkipList 支持有序范围查询与排序操作。
3. 两者配合实现“按 member 查”和“按 score 查”兼顾。

## 应用场景

1. 排行榜。
2. 延迟队列（按时间戳 score）。
3. 区间统计与分页。

## 高频面试点

1. ZSet 如何实现的？
2. SkipList 的层级结构与查找复杂度。
3. ZSet 与 TreeMap/B+Tree 在读写模式上的差异。

## 延伸问题

1. 大 key 排行榜如何分片？
2. 频繁更新 score 的性能瓶颈如何定位？

