# Publisher + Listener / Observer 模式落地实践

## 模式概述

**Publisher + Listener** 模式是观察者模式（Observer Pattern）和发布-订阅模式（Pub-Sub Pattern）的结合，用于实现业务解耦，将主流程与副产物逻辑（如发送通知、记录日志、更新缓存）分离。

## 核心组件

### 1. Event / Message（事件/消息）
事件载体，承载事件相关的数据。

```java
public abstract class DomainEvent {
    private final String eventId;
    private final LocalDateTime occurredTime;
    private final String eventType;
    
    protected DomainEvent(String eventType) {
        this.eventId = UUID.randomUUID().toString();
        this.occurredTime = LocalDateTime.now();
        this.eventType = eventType;
    }
    
    // getters
}
```

### 2. Publisher / EventSource（发布者）
触发事件的对象。

```java
public interface EventPublisher {
    /**
     * 发布事件
     */
    void publish(DomainEvent event);
    
    /**
     * 异步发布事件
     */
    void publishAsync(DomainEvent event);
}
```

### 3. Listener / Subscriber（监听者/订阅者）
订阅并处理事件的对象。

```java
public interface EventListener<T extends DomainEvent> {
    /**
     * 处理事件
     */
    void onEvent(T event);
    
    /**
     * 获取监听的事件类型
     */
    Class<T> getEventType();
    
    /**
     * 获取监听器优先级（数字越小优先级越高）
     */
    default int getOrder() {
        return 0;
    }
}
```

## 解决的问题

1. **业务耦合**：主业务逻辑与副产物逻辑（通知、日志）耦合在一起
2. **代码可维护性差**：通知逻辑散落在各个Service中
3. **难以扩展**：新增通知渠道需要修改业务代码
4. **性能影响**：同步执行副产物逻辑影响主流程性能

## 使用场景

- 订单创建后发送通知（邮件、短信、站内信）
- 用户注册后发送欢迎邮件、初始化用户数据
- 账户变动后更新缓存、记录审计日志
- 支付成功后触发后续流程

## 完整案例：订单事件系统

### 事件定义

#### 订单创建事件

```java
public class OrderCreatedEvent extends DomainEvent {
    private final Long orderId;
    private final Long userId;
    private final BigDecimal totalAmount;
    private final String orderNo;
    
    public OrderCreatedEvent(Long orderId, Long userId, BigDecimal totalAmount, String orderNo) {
        super("ORDER_CREATED");
        this.orderId = orderId;
        this.userId = userId;
        this.totalAmount = totalAmount;
        this.orderNo = orderNo;
    }
    
    // getters
}
```

#### 订单支付成功事件

```java
public class OrderPaidEvent extends DomainEvent {
    private final Long orderId;
    private final Long userId;
    private final BigDecimal paidAmount;
    private final String paymentId;
    
    public OrderPaidEvent(Long orderId, Long userId, BigDecimal paidAmount, String paymentId) {
        super("ORDER_PAID");
        this.orderId = orderId;
        this.userId = userId;
        this.paidAmount = paidAmount;
        this.paymentId = paymentId;
    }
    
    // getters
}
```

#### 订单发货事件

```java
public class OrderShippedEvent extends DomainEvent {
    private final Long orderId;
    private final Long userId;
    private final String shippingNo;
    private final String logisticsCompany;
    
    public OrderShippedEvent(Long orderId, Long userId, String shippingNo, String logisticsCompany) {
        super("ORDER_SHIPPED");
        this.orderId = orderId;
        this.userId = userId;
        this.shippingNo = shippingNo;
        this.logisticsCompany = logisticsCompany;
    }
    
    // getters
}
```

### 事件发布器

```java
@Component
@RequiredArgsConstructor
public class SpringEventPublisher implements EventPublisher {
    
    private final ApplicationEventPublisher applicationEventPublisher;
    private final TaskExecutor taskExecutor;
    
    @Override
    public void publish(DomainEvent event) {
        applicationEventPublisher.publishEvent(event);
    }
    
    @Override
    public void publishAsync(DomainEvent event) {
        taskExecutor.execute(() -> {
            applicationEventPublisher.publishEvent(event);
        });
    }
}
```

### 事件监听器

#### 订单创建 - 发送通知

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderCreatedNotificationListener implements EventListener<OrderCreatedEvent> {
    
    private final EmailService emailService;
    private final SmsService smsService;
    private final PushNotificationService pushNotificationService;
    
    @Override
    @Async
    @EventListener(OrderCreatedEvent.class)
    public void onEvent(OrderCreatedEvent event) {
        try {
            log.info("处理订单创建事件: orderId={}", event.getOrderId());
            
            // 发送邮件通知
            emailService.sendOrderCreatedEmail(event.getUserId(), event.getOrderNo());
            
            // 发送短信通知
            smsService.sendOrderCreatedSms(event.getUserId(), event.getOrderNo());
            
            // 发送推送通知
            pushNotificationService.sendOrderCreatedPush(event.getUserId(), event.getOrderNo());
            
        } catch (Exception e) {
            log.error("处理订单创建事件失败: orderId={}", event.getOrderId(), e);
            // 事件处理失败不应该影响主流程，只记录日志
        }
    }
    
    @Override
    public Class<OrderCreatedEvent> getEventType() {
        return OrderCreatedEvent.class;
    }
    
    @Override
    public int getOrder() {
        return 100;  // 通知优先级较低
    }
}
```

#### 订单创建 - 更新用户统计

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderCreatedStatsListener implements EventListener<OrderCreatedEvent> {
    
    private final UserStatsService userStatsService;
    
    @Override
    @Async
    @EventListener(OrderCreatedEvent.class)
    public void onEvent(OrderCreatedEvent event) {
        try {
            log.info("更新用户订单统计: userId={}, orderId={}", event.getUserId(), event.getOrderId());
            
            // 更新用户订单数量
            userStatsService.incrementOrderCount(event.getUserId());
            
            // 更新用户订单总金额
            userStatsService.addOrderAmount(event.getUserId(), event.getTotalAmount());
            
        } catch (Exception e) {
            log.error("更新用户订单统计失败: userId={}, orderId={}", 
                event.getUserId(), event.getOrderId(), e);
        }
    }
    
    @Override
    public Class<OrderCreatedEvent> getEventType() {
        return OrderCreatedEvent.class;
    }
    
    @Override
    public int getOrder() {
        return 50;  // 统计优先级中等
    }
}
```

#### 订单创建 - 记录审计日志

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderCreatedAuditListener implements EventListener<OrderCreatedEvent> {
    
    private final AuditLogService auditLogService;
    
    @Override
    @Async
    @EventListener(OrderCreatedEvent.class)
    public void onEvent(OrderCreatedEvent event) {
        try {
            log.info("记录订单创建审计日志: orderId={}", event.getOrderId());
            
            AuditLog auditLog = new AuditLog();
            auditLog.setEventType("ORDER_CREATED");
            auditLog.setEventId(event.getEventId());
            auditLog.setOrderId(event.getOrderId());
            auditLog.setUserId(event.getUserId());
            auditLog.setOccurredTime(event.getOccurredTime());
            auditLog.setDetails("订单创建: 订单号=" + event.getOrderNo() + 
                ", 金额=" + event.getTotalAmount());
            
            auditLogService.save(auditLog);
            
        } catch (Exception e) {
            log.error("记录订单创建审计日志失败: orderId={}", event.getOrderId(), e);
        }
    }
    
    @Override
    public Class<OrderCreatedEvent> getEventType() {
        return OrderCreatedEvent.class;
    }
    
    @Override
    public int getOrder() {
        return 10;  // 审计日志优先级最高
    }
}
```

#### 订单支付成功 - 发送通知

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderPaidNotificationListener implements EventListener<OrderPaidEvent> {
    
    private final EmailService emailService;
    private final SmsService smsService;
    
    @Override
    @Async
    @EventListener(OrderPaidEvent.class)
    public void onEvent(OrderPaidEvent event) {
        try {
            log.info("发送订单支付成功通知: orderId={}", event.getOrderId());
            
            // 发送支付成功邮件
            emailService.sendOrderPaidEmail(event.getUserId(), event.getOrderId());
            
            // 发送支付成功短信
            smsService.sendOrderPaidSms(event.getUserId(), event.getOrderId());
            
        } catch (Exception e) {
            log.error("发送订单支付成功通知失败: orderId={}", event.getOrderId(), e);
        }
    }
    
    @Override
    public Class<OrderPaidEvent> getEventType() {
        return OrderPaidEvent.class;
    }
}
```

#### 订单发货 - 发送通知

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderShippedNotificationListener implements EventListener<OrderShippedEvent> {
    
    private final EmailService emailService;
    private final SmsService smsService;
    private final LogisticsService logisticsService;
    
    @Override
    @Async
    @EventListener(OrderShippedEvent.class)
    public void onEvent(OrderShippedEvent event) {
        try {
            log.info("发送订单发货通知: orderId={}, shippingNo={}", 
                event.getOrderId(), event.getShippingNo());
            
            // 发送发货通知邮件
            emailService.sendOrderShippedEmail(
                event.getUserId(), 
                event.getOrderId(), 
                event.getShippingNo(),
                event.getLogisticsCompany()
            );
            
            // 发送发货通知短信
            smsService.sendOrderShippedSms(
                event.getUserId(), 
                event.getShippingNo(),
                event.getLogisticsCompany()
            );
            
            // 同步物流信息到第三方平台
            logisticsService.syncShippingInfo(
                event.getOrderId(),
                event.getShippingNo(),
                event.getLogisticsCompany()
            );
            
        } catch (Exception e) {
            log.error("发送订单发货通知失败: orderId={}", event.getOrderId(), e);
        }
    }
    
    @Override
    public Class<OrderShippedEvent> getEventType() {
        return OrderShippedEvent.class;
    }
}
```

### 使用事件发布器

```java
@Service
@RequiredArgsConstructor
@Transactional
public class OrderService {
    
    private final OrderRepository orderRepository;
    private final EventPublisher eventPublisher;
    
    /**
     * 创建订单
     */
    public Long createOrder(CreateOrderRequest request) {
        // 1. 创建订单（主流程）
        Order order = new Order();
        order.setOrderNo(generateOrderNo());
        order.setUserId(request.getUserId());
        order.setTotalAmount(request.getTotalAmount());
        order.setStatus(OrderStatus.PENDING_PAYMENT);
        orderRepository.save(order);
        
        // 2. 发布订单创建事件（异步，不影响主流程）
        OrderCreatedEvent event = new OrderCreatedEvent(
            order.getId(),
            order.getUserId(),
            order.getTotalAmount(),
            order.getOrderNo()
        );
        eventPublisher.publishAsync(event);  // 异步发布，不阻塞主流程
        
        return order.getId();
    }
    
    /**
     * 支付订单
     */
    public void payOrder(Long orderId, PaymentInfo paymentInfo) {
        // 1. 处理支付（主流程）
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        PaymentResult result = paymentService.processPayment(order, paymentInfo);
        if (!result.isSuccess()) {
            throw new BusinessException("支付失败");
        }
        
        order.setStatus(OrderStatus.PAID);
        order.setPaymentId(result.getPaymentId());
        order.setPaymentTime(LocalDateTime.now());
        orderRepository.save(order);
        
        // 2. 发布订单支付成功事件（异步）
        OrderPaidEvent event = new OrderPaidEvent(
            order.getId(),
            order.getUserId(),
            order.getTotalAmount(),
            result.getPaymentId()
        );
        eventPublisher.publishAsync(event);
    }
    
    /**
     * 发货
     */
    public void shipOrder(Long orderId, ShippingInfo shippingInfo) {
        // 1. 更新订单状态（主流程）
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        order.setStatus(OrderStatus.SHIPPED);
        order.setShippingNo(shippingInfo.getShippingNo());
        order.setLogisticsCompany(shippingInfo.getLogisticsCompany());
        order.setShippingTime(LocalDateTime.now());
        orderRepository.save(order);
        
        // 2. 发布订单发货事件（异步）
        OrderShippedEvent event = new OrderShippedEvent(
            order.getId(),
            order.getUserId(),
            shippingInfo.getShippingNo(),
            shippingInfo.getLogisticsCompany()
        );
        eventPublisher.publishAsync(event);
    }
}
```

## 工程实践要点

### 1. 使用 Spring Events
Spring 提供了完善的事件机制，无需自己实现：

```java
// 配置类
@Configuration
@EnableAsync
public class EventConfig {
    
    @Bean
    public TaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("event-");
        executor.initialize();
        return executor;
    }
}

// 使用 @EventListener 注解
@Component
public class OrderCreatedListener {
    
    @Async
    @EventListener(OrderCreatedEvent.class)
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 处理逻辑
    }
}
```

### 2. 事件处理失败策略
事件处理失败不应该影响主流程，应该：
- 记录日志
- 可选：重试机制
- 可选：死信队列

```java
@Component
@Slf4j
public class OrderCreatedNotificationListener {
    
    @Retryable(value = Exception.class, maxAttempts = 3)
    @Async
    @EventListener(OrderCreatedEvent.class)
    public void onEvent(OrderCreatedEvent event) {
        try {
            // 处理逻辑
        } catch (Exception e) {
            log.error("处理订单创建事件失败: orderId={}", event.getOrderId(), e);
            // 可以发送到死信队列
            deadLetterQueue.send(event);
            throw e;  // 抛出异常以触发重试
        }
    }
    
    @Recover
    public void recover(Exception e, OrderCreatedEvent event) {
        log.error("订单创建事件处理失败，已重试3次: orderId={}", event.getOrderId(), e);
        // 记录到失败队列或发送告警
    }
}
```

### 3. 事件顺序保证
如果需要保证事件的顺序，可以使用 `@Order` 注解：

```java
@Component
@Order(1)  // 优先级1，先执行
public class AuditLogListener implements EventListener<OrderCreatedEvent> {
    // ...
}

@Component
@Order(2)  // 优先级2，后执行
public class NotificationListener implements EventListener<OrderCreatedEvent> {
    // ...
}
```

### 4. 条件监听
支持条件监听，只在满足条件时处理事件：

```java
@Component
public class VipOrderListener {
    
    @Async
    @EventListener(condition = "#event.userId != null and @userService.isVip(#event.userId)")
    public void handleVipOrderCreated(OrderCreatedEvent event) {
        // 只处理VIP用户的订单
    }
}
```

## 与其他模式的组合

### Publisher + Listener + Strategy
根据不同事件类型使用不同的处理策略：

```java
public interface EventHandler {
    void handle(DomainEvent event);
    boolean supports(DomainEvent event);
}

@Component
public class EventHandlerFactory {
    
    private final List<EventHandler> handlers;
    
    public void handleEvent(DomainEvent event) {
        handlers.stream()
            .filter(handler -> handler.supports(event))
            .forEach(handler -> handler.handle(event));
    }
}
```

## 注意事项

1. **事件应该是不可变的**：一旦发布，不应该修改事件对象
2. **事件处理应该是幂等的**：多次处理同一事件应该产生相同的结果
3. **异步处理的异常处理**：异步处理失败不应该影响主流程
4. **性能考虑**：如果事件处理很重，应该使用异步处理

## 优势与劣势

### 优势
- ✅ 业务解耦，主流程与副产物逻辑分离
- ✅ 易于扩展，新增监听器无需修改业务代码
- ✅ 支持异步处理，不影响主流程性能
- ✅ 监听器可以独立测试

### 劣势
- ❌ 增加了代码复杂度
- ❌ 调试困难，需要追踪事件流转
- ❌ 异步处理的异常处理较复杂

## 适用场景判断

**适合使用 Publisher + Listener 的场景：**
- 主流程完成后需要执行多个副产物操作
- 副产物操作不应该影响主流程
- 需要支持异步处理提高性能
- 需要灵活扩展监听器

**不适合的场景：**
- 主流程必须等待副产物操作完成
- 副产物操作逻辑非常简单（1-2行代码）
- 不需要解耦的场景

