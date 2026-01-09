# CapitalFlowService 重构案例

**日期：** 2026-01-09  
**模块：** `capital-server/src/main/java/tech/tongyu/bct/capital/service/impl/CapitalFlowServiceImpl.java`  
**重构类型：** 策略模式重构 + 代码去重

## 重构背景

`CapitalFlowServiceImpl` 中的 `listTradeCashFlows` 和 `listMarginCashFlows` 方法存在以下问题：

1. **深层嵌套的 if-else**：`listTradeCashFlows` 方法包含 80+ 行的复杂条件判断
2. **代码重复**：两个方法有大量重复的代码块（获取单据ID、初始化DTO、遍历处理）
3. **违反开闭原则**：新增现金流类型需要修改主方法
4. **可维护性差**：业务逻辑散乱，难以定位和修改

## 重构前代码

### listTradeCashFlows 方法（重构前）

```java
private List<CapitalFlowDTO> listTradeCashFlows(CapitalFlowCriteria criteria) {
    List<CapitalFlowDTO> capitalFlows = new ArrayList<>();
    if (CollUtil.containsAny(TRADE_CASH_FLOW_TYPES, criteria.getCapitalFlowTypes()) || criteria.getCapitalFlowTypes() == null) {
        // ... 构建查询
        List<CashFlowViewDTO> cashFlows = tradeCashFlowService.listUnPaged(queryDTO);
        
        // 获取单据ID（重复代码）
        Map<String, String> openDocumentId = new HashMap<>();
        Map<String, String> unwindDocumentId = new HashMap<>();
        if (ORDER_NO_TYPE_CONFIRMATION_DOCUMENT_ID.equals(...)) {
            // ... 获取逻辑
        }
        
        // 80+ 行的 if-else 嵌套
        for (CashFlowViewDTO cashFlow : cashFlows) {
            CapitalFlowDTO dto = new CapitalFlowDTO();
            dto.setAmount(cashFlow.getCashFlowAmount());
            // ... 初始化
            
            if (CollUtil.contains(...) && cashFlow.getEventType() == OPEN && ...) {
                // 买入费用处理
            } else if (CollUtil.contains(...) && cashFlow.getEventType() == UNWIND && ...) {
                // 卖出费用处理
            } else if (...) {
                // ... 更多嵌套判断
            }
            // ... 10+ 个 else if 分支
        }
    }
    // 汇总逻辑
    return realCapitalFlows;
}
```

## 重构方案

### 1. 创建 Handler 接口和实现类

**接口定义：**
```java
public interface TradeCashFlowHandler {
    boolean supports(CashFlowViewDTO cashFlow, CapitalFlowCriteria criteria);
    void handle(CashFlowViewDTO cashFlow, CapitalFlowDTO dto, 
                Map<String, String> openIdMap, Map<String, String> unwindIdMap);
}
```

**具体实现示例：**
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
        if (cashFlow.getEventType() == OPEN) {
            dto.setCapitalFlowType(BUY_FEE);
            dto.setDisplayName(BUY_FEE.getDescription() + getOrderNum(...));
            dto.setDirection(PaymentDirectionEnum.OUT);
        } else if (cashFlow.getEventType() == UNWIND) {
            dto.setCapitalFlowType(SELL_FEE);
            dto.setDisplayName(SELL_FEE.getDescription() + getOrderNum(...));
            dto.setDirection(PaymentDirectionEnum.IN);
        }
    }
}
```

### 2. 创建 Factory 工厂类

```java
@Component
@RequiredArgsConstructor
public class TradeCashFlowHandlerFactory {
    private final List<TradeCashFlowHandler> handlers;  // Spring 自动注入

    public Optional<TradeCashFlowHandler> getHandler(
            CashFlowViewDTO cashFlow, 
            CapitalFlowCriteria criteria) {
        return handlers.stream()
                .filter(handler -> handler.supports(cashFlow, criteria))
                .findFirst();
    }
}
```

### 3. 提取公共方法

**提取单据ID获取逻辑：**
```java
private Map<String, Map<String, String>> fetchConfirmationDocumentIds(
        List<CashFlowViewDTO> cashFlows) {
    // 统一的获取逻辑，供多个方法复用
}
```

**提取DTO初始化逻辑：**
```java
private CapitalFlowDTO initBaseCapitalFlowDTO(CashFlowViewDTO cashFlow) {
    // 统一的初始化逻辑
}
```

**提取通用处理方法：**
```java
@FunctionalInterface
interface CashFlowHandlerApplier {
    void apply(CashFlowViewDTO cashFlow, CapitalFlowCriteria criteria, 
               CapitalFlowDTO dto, Map<String, String> openIdMap, 
               Map<String, String> unwindIdMap);
}

private List<CapitalFlowDTO> processCashFlows(
        List<CashFlowViewDTO> cashFlows,
        CapitalFlowCriteria criteria,
        CashFlowHandlerApplier handlerApplier) {
    // 统一的处理流程
}
```

### 4. 重构后的方法

```java
private List<CapitalFlowDTO> listTradeCashFlows(CapitalFlowCriteria criteria) {
    if (!CollUtil.containsAny(TRADE_CASH_FLOW_TYPES, criteria.getCapitalFlowTypes()) 
            && criteria.getCapitalFlowTypes() != null) {
        return Collections.emptyList();
    }

    // 构建查询
    CashFlowQueryDTO queryDTO = buildQuery(criteria);
    List<CashFlowViewDTO> cashFlows = tradeCashFlowService.listUnPaged(queryDTO);

    // 使用通用方法处理（函数式调用）
    List<CapitalFlowDTO> capitalFlows = processCashFlows(cashFlows, criteria, 
        (cashFlow, crit, dto, openIdMap, unwindIdMap) -> 
            tradeCashFlowHandlerFactory.getHandler(cashFlow, crit)
                .ifPresent(handler -> handler.handle(cashFlow, dto, openIdMap, unwindIdMap))
    );

    // 聚合处理
    return aggregateCapitalFlows(capitalFlows, noAggregateTypes, aggregateTypes);
}
```

## 重构成果

### 代码质量提升

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| `listTradeCashFlows` 行数 | ~100行 | ~30行 | ↓70% |
| `listMarginCashFlows` 行数 | ~50行 | ~25行 | ↓50% |
| 重复代码行数 | ~50行 | 0行 | ↓100% |
| Handler 类数量 | 0 | 8个 | 职责清晰 |
| 可测试性 | 低（需Mock整个Service） | 高（可单独测试Handler） | ↑ |

### 架构改进

1. **符合开闭原则**：新增现金流类型只需新增 Handler 类
2. **单一职责**：每个 Handler 只负责一种业务逻辑
3. **代码复用**：公共逻辑提取到通用方法
4. **函数式编程**：使用 Lambda 表达式，代码更简洁

## 创建的 Handler 列表

1. `TradeFeeHandler` - 交易费用处理（买入/卖出费用）
2. `EquityIncomeHandler` - 权益收入处理（买入/卖出成交）
3. `DividendHandler` - 分红处理
4. `CapitalAdjustHandler` - 资金调整处理
5. `InterestDeductionHandler` - 利息扣除处理
6. `PremiumHandler` - 期权费处理
7. `PaymentOptionHandler` - 期权结算金额处理
8. `ExtensionFeeHandler` - 展期费用处理

## 关键学习点

### 1. Spring 的 List 注入优于 Map
使用 `List<TradeCashFlowHandler>` 配合 `supports()` 方法，比手动维护 Map 更优雅。

### 2. 函数式接口简化调用
通过 `CashFlowHandlerApplier` 函数式接口，将 Handler 的选择和应用逻辑解耦。

### 3. 抽象基类提取公共逻辑
`AbstractTradeCashFlowHandler` 提供了 `getOrderNum()` 等公共方法，避免代码重复。

### 4. 模板方法模式的应用
`processCashFlows` 方法定义了统一的处理流程，具体的 Handler 应用逻辑通过函数式接口注入。

## 后续优化建议

1. **性能优化**：如果 Handler 数量很多，可以考虑使用 Map 缓存 `supports()` 的结果
2. **优先级支持**：如果需要 Handler 优先级，可以使用 `@Order` 注解
3. **单元测试**：为每个 Handler 编写独立的单元测试
4. **文档完善**：为每个 Handler 添加详细的业务规则说明

## 相关模式

- [Factory + Handler 模式](../patterns/factory-handler-pattern.md)

