# GoF 23 模式总览

## 定义

GoF（Gang of Four）23 模式是面向对象设计中反复出现的 **可复用解决方案模板**，按职责分为创建型（5）、结构型（7）、行为型（11）。模式不是语法，而是 **在特定约束下平衡变化与稳定** 的结构手段。

## 分类速查

### 创建型（5）— 对象如何创建

| 模式 | 定义 | 适用场景 | 反例 / 误用 | 框架映射 |
|------|------|----------|-------------|----------|
| 单例 Singleton | 全局唯一实例 | 配置中心、线程池、连接池 | 滥用导致全局状态、测试困难 | Spring 默认 Bean 单例 |
| 工厂方法 Factory Method | 子类决定实例化哪个产品 | 产品族扩展、创建逻辑分散 | 产品类型固定仍套工厂 | `Calendar.getInstance()` |
| 抽象工厂 Abstract Factory | 创建一族相关产品 | UI 主题、跨 DB 驱动族 | 只有单一产品族 | Spring `BeanFactory` |
| 建造者 Builder | 分步构建复杂对象 | 多可选参数、不可变对象 | 字段少且固定仍用 Builder | Lombok `@Builder`、`StringBuilder` |
| 原型 Prototype | 克隆已有对象 | 创建成本高、需保留初始状态 | 浅拷贝导致共享可变引用 | `Object.clone()`、深拷贝工具 |

### 结构型（7）— 类与对象如何组合

| 模式 | 定义 | 适用场景 | 反例 / 误用 | 框架映射 |
|------|------|----------|-------------|----------|
| 适配器 Adapter | 转换接口使不兼容类协同 | 对接第三方 SDK、遗留 API | 能改接口源码仍硬套 Adapter | JDBC-ODBC 桥、Spring MVC HandlerAdapter |
| 桥接 Bridge | 抽象与实现分离，独立变化 | 多维度扩展（消息×发送渠道） | 维度单一 | JDBC `Driver` / `Connection` 分离 |
| 组合 Composite | 树形结构统一对待叶子与容器 | 菜单、组织架构、表达式树 | 扁平列表强行树化 | Java `File` / `FileSystem` |
| 装饰器 Decorator | 动态叠加职责 | 流式增强、权限包装 | 继承链爆炸 | Java IO 流、`Collections.synchronizedList` |
| 外观 Facade | 简化子系统入口 | 复杂模块对外统一 API | Facade 含业务逻辑 | SLF4J、`JdbcTemplate` |
| 享元 Flyweight | 共享细粒度对象降内存 | 字符池、棋子、连接元数据 | 对象无重复仍享元 | `Integer.valueOf` 缓存 -128~127 |
| 代理 Proxy | 控制访问、增强行为 | 远程调用、懒加载、权限 | 简单 CRUD 套多层代理 | Spring AOP、MyBatis Mapper 代理 |

### 行为型（11）— 对象如何协作

| 模式 | 定义 | 适用场景 | 反例 / 误用 | 框架映射 |
|------|------|----------|-------------|----------|
| 责任链 Chain of Responsibility | 请求沿链传递直至处理 | 过滤器、审批流、Pipeline | 链过长且无短路监控 | Servlet Filter、Netty Pipeline |
| 命令 Command | 请求封装为对象 | 撤销/重做、异步队列、审计 | 无参数方法硬封装 Command | `Runnable`、MQ 消息体 |
| 解释器 Interpreter | 语法规则类化 | 简单 DSL、表达式 | 复杂语法仍用解释器 | SpEL（部分思想） |
| 迭代器 Iterator | 顺序访问聚合而不暴露内部 | 统一遍历多种容器 | 已有 Stream 仍手写 Iterator | Java `Iterator`、`Stream` |
| 中介者 Mediator | 对象经中介通信，降低耦合 | 聊天室、表单字段联动 | 中介者变成上帝类 | Spring Event、消息总线 |
| 备忘录 Memento | 保存/恢复对象状态 | 编辑器撤销、快照 | 大对象频繁快照 | Git、数据库事务回滚点 |
| 观察者 Observer | 一对多状态通知 | 事件驱动、UI 绑定 | 同步通知导致循环依赖 | Spring `@EventListener`、MQ 发布订阅 |
| 状态 State | 状态行为封装，切换改变行为 | 订单/合约状态机 | 大量 if-else 未抽取 | 期权生命周期状态机 |
| 策略 Strategy | 算法族可互换 | 计费规则、路由、校验 | 策略类爆炸无注册表 | `Comparator`、Factory+Handler |
| 模板方法 Template Method | 骨架固定，步骤子类实现 | 固定流程可变细节 | 钩子过多难维护 | `AbstractList`、`JdbcTemplate` |
| 访问者 Visitor | 数据结构与操作分离 | 编译器 AST、报表导出 | 数据结构频繁变更 | ASM 字节码访问 |

## 落地模板（选型四问）

1. **变化点是什么？** 创建方式 / 结构组合 / 行为算法 — 决定创建型 / 结构型 / 行为型。
2. **稳定点是什么？** 客户端依赖的接口应稳定，变化封装在子类或组合对象内。
3. **扩展方式？** 优先组合 + 接口，避免深层继承。
4. **有无现成落地？** 查框架映射与 [模式落地实践](../../模式落地实践/) 中的项目案例。

## 与本库落地文档的映射

| GoF 模式 | 本库落地文档 |
|----------|--------------|
| 策略 + 工厂方法 | [Factory + Handler](../../模式落地实践/factory-handler-pattern.md) |
| 适配器 + 代理 | [Adapter + Provider](../../模式落地实践/adapter-provider-pattern.md) |
| 建造者 | [Builder + Director](../../模式落地实践/builder-director-pattern.md) |
| 状态 | [State + Machine / Engine](../../模式落地实践/State%20+%20Machine或Engine%20模式落地实践.md) |
| 装饰器 + 适配 | [Converter / Mapper + Decorator](../../模式落地实践/Converter%20或%20Mapper%20+%20Decorator%20模式落地实践.md) |
| 观察者 | [Publisher + Listener / Observer](../../模式落地实践/Publisher%20+%20Listener或Observer%20模式落地实践.md) |
| 责任链 | [责任链 / Pipeline + Stage](../../模式落地实践/责任链模式.md) |

## 高频面试点

1. 策略 vs 工厂 vs 模板方法：策略替换整段算法；工厂负责创建；模板方法固定流程骨架。
2. 装饰器 vs 代理：装饰器侧重 **叠加职责**；代理侧重 **访问控制**（延迟、权限、远程）。
3. 桥接 vs 适配器：桥接 **设计期** 分离抽象与实现；适配器 **运行期** 兼容已有接口。
4. 观察者 vs 发布订阅：观察者通常同步、耦合在同一进程；发布订阅经 Broker 解耦、可异步跨进程。

## 延伸问题

1. 单例在 Spring 与 DCL 手写实现中的线程安全差异？
2. 为什么 Spring 推荐构造器注入而非 field 注入？（与可测试性、不可变性相关）
