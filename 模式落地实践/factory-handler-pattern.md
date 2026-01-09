# Factory + Handler 模式落地实践

## 模式概述

**Factory + Handler** 是策略模式（Strategy Pattern）在企业级 Java 开发中的常见落地形式，通过 Spring 的依赖注入机制实现策略的自动发现和选择。

## 核心组件

### 1. Handler 接口
定义策略的统一接口，包含两个核心方法：
- `supports()`: 判断是否支持处理当前数据
- `handle()`: 执行具体的处理逻辑

```java
public interface TradeCashFlowHandler {
    boolean supports(CashFlowViewDTO cashFlow, CapitalFlowCriteria criteria);
    void handle(CashFlowViewDTO cashFlow, CapitalFlowDTO dto, 
                Map<String, String> openIdMap, Map<String, String> unwindIdMap);
}
```

### 2. 具体 Handler 实现
每个 Handler 负责处理一种特定的业务场景，使用 `@Component` 注解让 Spring 自动管理。

```java
@Component
public class TradeFeeHandler extends AbstractTradeCashFlowHandler {
    @Override
    public boolean supports(CashFlowViewDTO cashFlow, CapitalFlowCriteria criteria) {
        return CollUtil.contains(Arrays.asList(OPEN, UNWIND, SETTLE), cashFlow.getEventType()) 
                && cashFlow.getCashFlowType() == TRADE_FEE;
    }

    @Override
    public void handle(CashFlowViewDTO cashFlow, CapitalFlowDTO dto, ...) {
        // 具体处理逻辑
    }
}
```

### 3. Factory 工厂类
通过 Spring 自动注入所有 Handler 实现，提供查找匹配 Handler 的方法。

```java
@Component
@RequiredArgsConstructor
public class TradeCashFlowHandlerFactory {
    private final List<TradeCashFlowHandler> handlers;  // Spring 自动注入所有实现

    public Optional<TradeCashFlowHandler> getHandler(
            CashFlowViewDTO cashFlow, 
            CapitalFlowCriteria criteria) {
        return handlers.stream()
                .filter(handler -> handler.supports(cashFlow, criteria))
                .findFirst();
    }
}
```

## 解决的问题

1. **消除深层嵌套的 if-else**：将复杂的条件判断分散到各个 Handler 中
2. **违反开闭原则**：新增业务类型时，只需新增 Handler 类，无需修改主服务类
3. **代码可测试性差**：每个 Handler 可以独立进行单元测试
4. **逻辑散乱**：每个业务规则都有明确的归属地

## 使用场景

- 根据不同的输入类型执行不同的处理逻辑
- 需要频繁扩展新的处理类型
- 处理逻辑复杂，包含多层条件判断
- 希望提高代码的可维护性和可测试性

## 工程实践要点

### 1. 使用 Spring 的 List 注入而非 Map
**推荐做法：**
```java
private final List<TradeCashFlowHandler> handlers;  // Spring 自动注入所有实现
```

**不推荐：**
```java
private final Map<String, TradeCashFlowHandler> handlerMap;  // 需要手动注册
```

**原因：** Spring 的 List 注入更简洁，配合 `supports()` 方法可以实现更灵活的选择逻辑。

### 2. 抽象基类提取公共逻辑
如果多个 Handler 有共同的逻辑（如获取单据编号），可以创建抽象基类：

```java
public abstract class AbstractTradeCashFlowHandler implements TradeCashFlowHandler {
    protected final SystemVariableCache systemVariableCache;
    
    protected String getOrderNum(CashFlowViewDTO cashFlow, ...) {
        // 公共逻辑
    }
}
```

### 3. 函数式接口简化调用
使用函数式接口和 Lambda 表达式，让调用代码更简洁：

```java
@FunctionalInterface
interface CashFlowHandlerApplier {
    void apply(CashFlowViewDTO cashFlow, CapitalFlowCriteria criteria, 
               CapitalFlowDTO dto, Map<String, String> openIdMap, 
               Map<String, String> unwindIdMap);
}

// 使用
processCashFlows(cashFlows, criteria, 
    (cashFlow, crit, dto, openIdMap, unwindIdMap) -> 
        factory.getHandler(cashFlow, crit)
            .ifPresent(handler -> handler.handle(cashFlow, dto, openIdMap, unwindIdMap))
);
```

## 与其他模式的组合

### Factory + Handler + Template Method
当多个 Handler 有共同的执行流程时，可以结合模板方法模式：

```java
public abstract class AbstractHandler {
    public final void execute(Context context) {
        prepare(context);      // 模板方法
        doHandle(context);     // 子类实现
        afterHandle(context);  // 模板方法
    }
    
    protected abstract void doHandle(Context context);
}
```

## 注意事项

1. **Handler 的优先级**：如果多个 Handler 的 `supports()` 都返回 true，`findFirst()` 会返回第一个匹配的。如果需要优先级，可以使用 `@Order` 注解或自定义排序。

2. **性能考虑**：如果 Handler 数量很多，可以考虑使用 Map 缓存 `supports()` 的结果，避免每次都遍历。

3. **空值处理**：使用 `Optional` 包装返回值，避免空指针异常。

## 参考案例

- [CapitalFlowService 重构案例](../refactoring/2026-01-09-capital-flow-refactoring.md)

