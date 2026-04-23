# JDK - JUC 核心问题

## 定义

JUC（`java.util.concurrent`）是 JDK 并发工具包，提供锁、并发容器、线程池与同步器。

## 原理

1. 通过 CAS、volatile 与队列同步器降低阻塞开销。
2. 使用 AQS 统一抽象锁与同步器实现。
3. 通过阻塞队列协调生产消费与线程调度。

## 应用场景

1. 高并发服务开发。
2. 异步任务处理。
3. 线程协作与限流。

## 高频面试点

1. 加锁解锁性能为什么高？
2. CLH 队列怎样的结构？
3. 阻塞队列有哪些？
   - `ArrayBlockingQueue`
   - `LinkedBlockingQueue`
   - `SynchronousQueue`
   - `PriorityBlockingQueue`
   - `DelayQueue`

## 延伸问题

1. ReentrantLock 与 synchronized 的选型边界是什么？
2. AQS 如何实现公平锁与非公平锁？

