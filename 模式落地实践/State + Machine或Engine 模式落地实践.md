# State + Machine / Engine 模式落地实践

## 模式概述

**State + Machine** 模式是状态模式（State Pattern）的增强版本，通过状态机（State Machine）来管理对象在不同状态下的行为转换，特别适用于复杂的业务状态流转场景。

## 核心组件

### 1. State（状态）
定义状态接口，每个状态封装该状态下的行为。

```java
public interface OrderState {
    /**
     * 状态名称
     */
    String getName();
    
    /**
     * 支付操作
     */
    void pay(OrderContext context);
    
    /**
     * 取消操作
     */
    void cancel(OrderContext context);
    
    /**
     * 发货操作
     */
    void ship(OrderContext context);
    
    /**
     * 确认收货操作
     */
    void confirm(OrderContext context);
    
    /**
     * 退款操作
     */
    void refund(OrderContext context);
}
```

### 2. StateMachine / Engine（状态机）
负责维护当前状态，并根据事件执行状态流转。

```java
@Component
@RequiredArgsConstructor
public class OrderStateMachine {
    
    private final Map<OrderStatus, OrderState> stateMap;
    
    /**
     * 执行状态转换
     */
    public void transition(Order order, OrderEvent event) {
        OrderStatus currentStatus = order.getStatus();
        OrderState currentState = stateMap.get(currentStatus);
        
        if (currentState == null) {
            throw new IllegalStateException("未知状态: " + currentStatus);
        }
        
        // 创建上下文
        OrderContext context = new OrderContext(order, event);
        
        // 根据事件类型执行相应操作
        switch (event.getType()) {
            case PAY:
                currentState.pay(context);
                break;
            case CANCEL:
                currentState.cancel(context);
                break;
            case SHIP:
                currentState.ship(context);
                break;
            case CONFIRM:
                currentState.confirm(context);
                break;
            case REFUND:
                currentState.refund(context);
                break;
            default:
                throw new IllegalArgumentException("未知事件类型: " + event.getType());
        }
        
        // 更新订单状态
        order.setStatus(context.getNewStatus());
        order.setLastUpdateTime(LocalDateTime.now());
    }
    
    /**
     * 获取当前状态对象
     */
    public OrderState getCurrentState(Order order) {
        return stateMap.get(order.getStatus());
    }
}
```

### 3. Context（上下文）
承载状态转换时需要的上下文信息。

```java
public class OrderContext {
    private final Order order;
    private final OrderEvent event;
    private OrderStatus newStatus;
    private String errorMessage;
    
    public OrderContext(Order order, OrderEvent event) {
        this.order = order;
        this.event = event;
    }
    
    // getters and setters
}
```

## 解决的问题

1. **复杂的 if-else 状态判断**：将状态相关的逻辑封装到对应的 State 类中
2. **状态转换规则不清晰**：通过状态机明确状态转换规则
3. **违反开闭原则**：新增状态只需新增 State 类，无需修改现有代码
4. **状态转换错误**：状态机可以验证状态转换的合法性

## 使用场景

- 订单状态流转（待支付 -> 已支付 -> 已发货 -> 已收货 -> 已完成）
- 审批流程状态（待提交 -> 审批中 -> 已通过/已拒绝）
- 工单状态管理（待处理 -> 处理中 -> 已完成 -> 已关闭）
- 账户状态管理（正常 -> 冻结 -> 注销）

## 完整案例：订单状态机

### 状态定义

#### 待支付状态

```java
@Component
public class PendingPaymentState implements OrderState {
    
    private final OrderRepository orderRepository;
    private final PaymentService paymentService;
    
    @Override
    public String getName() {
        return "待支付";
    }
    
    @Override
    public void pay(OrderContext context) {
        Order order = context.getOrder();
        
        // 执行支付
        PaymentResult result = paymentService.processPayment(order);
        
        if (result.isSuccess()) {
            order.setPaymentId(result.getPaymentId());
            order.setPaymentTime(LocalDateTime.now());
            context.setNewStatus(OrderStatus.PAID);
            orderRepository.save(order);
        } else {
            context.setErrorMessage("支付失败: " + result.getMessage());
            throw new BusinessException("支付失败");
        }
    }
    
    @Override
    public void cancel(OrderContext context) {
        Order order = context.getOrder();
        order.setCancelReason(context.getEvent().getReason());
        order.setCancelTime(LocalDateTime.now());
        context.setNewStatus(OrderStatus.CANCELLED);
        orderRepository.save(order);
    }
    
    @Override
    public void ship(OrderContext context) {
        throw new IllegalStateException("待支付状态不能发货");
    }
    
    @Override
    public void confirm(OrderContext context) {
        throw new IllegalStateException("待支付状态不能确认收货");
    }
    
    @Override
    public void refund(OrderContext context) {
        throw new IllegalStateException("待支付状态不能退款");
    }
}
```

#### 已支付状态

```java
@Component
public class PaidState implements OrderState {
    
    private final OrderRepository orderRepository;
    private final RefundService refundService;
    
    @Override
    public String getName() {
        return "已支付";
    }
    
    @Override
    public void pay(OrderContext context) {
        throw new IllegalStateException("已支付状态不能重复支付");
    }
    
    @Override
    public void cancel(OrderContext context) {
        // 已支付状态取消需要退款
        Order order = context.getOrder();
        
        // 执行退款
        RefundResult result = refundService.refund(order);
        if (result.isSuccess()) {
            order.setCancelReason(context.getEvent().getReason());
            order.setCancelTime(LocalDateTime.now());
            context.setNewStatus(OrderStatus.CANCELLED);
            orderRepository.save(order);
        } else {
            context.setErrorMessage("退款失败: " + result.getMessage());
            throw new BusinessException("退款失败");
        }
    }
    
    @Override
    public void ship(OrderContext context) {
        Order order = context.getOrder();
        order.setShippingTime(LocalDateTime.now());
        order.setShippingNo(context.getEvent().getShippingNo());
        context.setNewStatus(OrderStatus.SHIPPED);
        orderRepository.save(order);
    }
    
    @Override
    public void confirm(OrderContext context) {
        throw new IllegalStateException("已支付状态不能确认收货，请先发货");
    }
    
    @Override
    public void refund(OrderContext context) {
        Order order = context.getOrder();
        RefundResult result = refundService.refund(order);
        if (result.isSuccess()) {
            context.setNewStatus(OrderStatus.REFUNDED);
            orderRepository.save(order);
        } else {
            context.setErrorMessage("退款失败: " + result.getMessage());
            throw new BusinessException("退款失败");
        }
    }
}
```

#### 已发货状态

```java
@Component
public class ShippedState implements OrderState {
    
    private final OrderRepository orderRepository;
    
    @Override
    public String getName() {
        return "已发货";
    }
    
    @Override
    public void pay(OrderContext context) {
        throw new IllegalStateException("已发货状态不能支付");
    }
    
    @Override
    public void cancel(OrderContext context) {
        throw new IllegalStateException("已发货状态不能取消，请联系客服");
    }
    
    @Override
    public void ship(OrderContext context) {
        throw new IllegalStateException("已发货状态不能重复发货");
    }
    
    @Override
    public void confirm(OrderContext context) {
        Order order = context.getOrder();
        order.setConfirmTime(LocalDateTime.now());
        context.setNewStatus(OrderStatus.CONFIRMED);
        orderRepository.save(order);
    }
    
    @Override
    public void refund(OrderContext context) {
        throw new IllegalStateException("已发货状态不能退款，请先确认收货后再申请退款");
    }
}
```

#### 已完成状态

```java
@Component
public class CompletedState implements OrderState {
    
    @Override
    public String getName() {
        return "已完成";
    }
    
    @Override
    public void pay(OrderContext context) {
        throw new IllegalStateException("已完成状态不能支付");
    }
    
    @Override
    public void cancel(OrderContext context) {
        throw new IllegalStateException("已完成状态不能取消");
    }
    
    @Override
    public void ship(OrderContext context) {
        throw new IllegalStateException("已完成状态不能发货");
    }
    
    @Override
    public void confirm(OrderContext context) {
        throw new IllegalStateException("已完成状态不能重复确认收货");
    }
    
    @Override
    public void refund(OrderContext context) {
        throw new IllegalStateException("已完成状态不支持退款，请走售后流程");
    }
}
```

### 事件定义

```java
public enum OrderEventType {
    PAY,      // 支付
    CANCEL,   // 取消
    SHIP,     // 发货
    CONFIRM,  // 确认收货
    REFUND    // 退款
}

public class OrderEvent {
    private final OrderEventType type;
    private String reason;
    private String shippingNo;
    private Map<String, Object> params = new HashMap<>();
    
    public OrderEvent(OrderEventType type) {
        this.type = type;
    }
    
    // getters and setters
}
```

### 状态机配置

```java
@Configuration
public class OrderStateMachineConfig {
    
    @Bean
    public Map<OrderStatus, OrderState> orderStateMap(
            PendingPaymentState pendingPaymentState,
            PaidState paidState,
            ShippedState shippedState,
            ConfirmedState confirmedState,
            CompletedState completedState,
            CancelledState cancelledState,
            RefundedState refundedState) {
        
        Map<OrderStatus, OrderState> stateMap = new HashMap<>();
        stateMap.put(OrderStatus.PENDING_PAYMENT, pendingPaymentState);
        stateMap.put(OrderStatus.PAID, paidState);
        stateMap.put(OrderStatus.SHIPPED, shippedState);
        stateMap.put(OrderStatus.CONFIRMED, confirmedState);
        stateMap.put(OrderStatus.COMPLETED, completedState);
        stateMap.put(OrderStatus.CANCELLED, cancelledState);
        stateMap.put(OrderStatus.REFUNDED, refundedState);
        
        return stateMap;
    }
}
```

### 使用状态机

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    
    private final OrderStateMachine stateMachine;
    
    /**
     * 支付订单
     */
    public void payOrder(Long orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        OrderEvent event = new OrderEvent(OrderEventType.PAY);
        stateMachine.transition(order, event);
    }
    
    /**
     * 取消订单
     */
    public void cancelOrder(Long orderId, String reason) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        OrderEvent event = new OrderEvent(OrderEventType.CANCEL);
        event.setReason(reason);
        stateMachine.transition(order, event);
    }
    
    /**
     * 发货
     */
    public void shipOrder(Long orderId, String shippingNo) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        OrderEvent event = new OrderEvent(OrderEventType.SHIP);
        event.setShippingNo(shippingNo);
        stateMachine.transition(order, event);
    }
}
```

## 工程实践要点

### 1. 使用枚举定义状态
```java
public enum OrderStatus {
    PENDING_PAYMENT("待支付"),
    PAID("已支付"),
    SHIPPED("已发货"),
    CONFIRMED("已确认收货"),
    COMPLETED("已完成"),
    CANCELLED("已取消"),
    REFUNDED("已退款");
    
    private final String description;
    
    OrderStatus(String description) {
        this.description = description;
    }
}
```

### 2. 状态转换规则验证
在状态机中验证状态转换的合法性：

```java
public class OrderStateMachine {
    
    // 定义合法的状态转换
    private static final Map<OrderStatus, Set<OrderStatus>> VALID_TRANSITIONS = Map.of(
        OrderStatus.PENDING_PAYMENT, Set.of(OrderStatus.PAID, OrderStatus.CANCELLED),
        OrderStatus.PAID, Set.of(OrderStatus.SHIPPED, OrderStatus.CANCELLED, OrderStatus.REFUNDED),
        OrderStatus.SHIPPED, Set.of(OrderStatus.CONFIRMED),
        OrderStatus.CONFIRMED, Set.of(OrderStatus.COMPLETED)
    );
    
    public void transition(Order order, OrderEvent event) {
        OrderStatus currentStatus = order.getStatus();
        OrderState currentState = stateMap.get(currentStatus);
        
        // 先执行状态的操作（操作中会设置新状态）
        // ...执行操作...
        
        // 验证状态转换是否合法
        OrderStatus newStatus = context.getNewStatus();
        if (!isValidTransition(currentStatus, newStatus)) {
            throw new IllegalStateException(
                String.format("状态转换不合法: %s -> %s", currentStatus, newStatus));
        }
    }
    
    private boolean isValidTransition(OrderStatus from, OrderStatus to) {
        Set<OrderStatus> validTargets = VALID_TRANSITIONS.get(from);
        return validTargets != null && validTargets.contains(to);
    }
}
```

### 3. 支持状态转换监听
支持在状态转换时触发监听器：

```java
public interface StateTransitionListener {
    void onTransition(OrderStatus from, OrderStatus to, Order order);
}

@Component
public class OrderStatusChangeListener implements StateTransitionListener {
    
    private final EventPublisher eventPublisher;
    
    @Override
    public void onTransition(OrderStatus from, OrderStatus to, Order order) {
        // 发布状态变更事件
        eventPublisher.publish(new OrderStatusChangedEvent(from, to, order));
        
        // 发送通知
        if (to == OrderStatus.SHIPPED) {
            notificationService.sendShippingNotification(order);
        }
    }
}
```

### 4. 状态持久化
状态变更应该记录到数据库，便于追溯：

```java
@Component
public class OrderStateHistoryService {
    
    public void recordStateChange(Order order, OrderStatus from, OrderStatus to, String reason) {
        OrderStateHistory history = new OrderStateHistory();
        history.setOrderId(order.getId());
        history.setFromStatus(from);
        history.setToStatus(to);
        history.setReason(reason);
        history.setCreateTime(LocalDateTime.now());
        historyRepository.save(history);
    }
}
```

## 与其他模式的组合

### State + Machine + Strategy
不同订单类型可以使用不同的状态机：

```java
public interface OrderStateMachineStrategy {
    OrderStateMachine getStateMachine(OrderType orderType);
}

@Component
public class DefaultOrderStateMachineStrategy implements OrderStateMachineStrategy {
    
    private final NormalOrderStateMachine normalOrderStateMachine;
    private final VipOrderStateMachine vipOrderStateMachine;
    
    @Override
    public OrderStateMachine getStateMachine(OrderType orderType) {
        switch (orderType) {
            case NORMAL:
                return normalOrderStateMachine;
            case VIP:
                return vipOrderStateMachine;
            default:
                return normalOrderStateMachine;
        }
    }
}
```

## 注意事项

1. **状态应该是不可变的**：一旦订单进入某个状态，不能直接修改状态字段，必须通过状态机转换
2. **状态转换应该是原子的**：状态转换和相关的业务操作应该在同一个事务中
3. **异常处理**：状态转换失败时，应该回滚到原始状态
4. **性能考虑**：如果状态转换很频繁，可以考虑使用状态机引擎（如 Spring State Machine）

## 优势与劣势

### 优势
- ✅ 状态转换规则清晰明确
- ✅ 符合开闭原则，易于扩展新状态
- ✅ 每个状态的行为封装独立，易于测试
- ✅ 防止非法状态转换

### 劣势
- ❌ 增加了代码复杂度
- ❌ 需要为每个状态创建一个类
- ❌ 状态转换链复杂时，调试较困难

## 适用场景判断

**适合使用 State + Machine 的场景：**
- 状态数量较多（>5个）
- 状态转换规则复杂
- 不同状态下同一操作的行为差异很大
- 需要防止非法状态转换

**不适合的场景：**
- 状态数量很少（<3个），简单的布尔状态
- 状态转换规则非常简单

