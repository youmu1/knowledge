# Adapter / Proxy + Provider 模式落地实践

## 模式概述

**Adapter / Proxy + Provider** 模式是适配器模式（Adapter Pattern）和代理模式（Proxy Pattern）的组合，用于屏蔽底层差异或第三方接口的复杂性，提供统一的接入标准。

## 核心组件

### 1. Provider（提供者接口）
定义统一的接入标准。

```java
public interface PaymentProvider {
    /**
     * 执行支付
     */
    PaymentResult pay(PaymentRequest request);
    
    /**
     * 查询支付结果
     */
    PaymentResult query(String paymentId);
    
    /**
     * 退款
     */
    RefundResult refund(RefundRequest request);
    
    /**
     * 获取支付渠道名称
     */
    String getProviderName();
    
    /**
     * 是否支持该支付方式
     */
    boolean supports(PaymentMethod paymentMethod);
}
```

### 2. Adapter（适配器实现）
将具体的第三方接口适配到 Provider 标准。

```java
@Component
public class AlipayAdapter implements PaymentProvider {
    
    private final AlipayClient alipayClient;
    
    @Override
    public PaymentResult pay(PaymentRequest request) {
        // 将统一的 PaymentRequest 转换为支付宝的请求格式
        AlipayTradePagePayRequest alipayRequest = convertToAlipayRequest(request);
        
        // 调用支付宝SDK
        AlipayTradePagePayResponse response = alipayClient.pageExecute(alipayRequest);
        
        // 将支付宝的响应转换为统一格式
        return convertToPaymentResult(response);
    }
    
    @Override
    public String getProviderName() {
        return "Alipay";
    }
    
    @Override
    public boolean supports(PaymentMethod paymentMethod) {
        return paymentMethod == PaymentMethod.ALIPAY || 
               paymentMethod == PaymentMethod.ALIPAY_H5;
    }
    
    private AlipayTradePagePayRequest convertToAlipayRequest(PaymentRequest request) {
        // 转换逻辑
    }
    
    private PaymentResult convertToPaymentResult(AlipayTradePagePayResponse response) {
        // 转换逻辑
    }
}
```

### 3. Proxy（代理）
在调用前后增加横切逻辑（如重试、限流、熔断）。

```java
@Component
@RequiredArgsConstructor
public class PaymentProviderProxy implements PaymentProvider {
    
    private final PaymentProvider targetProvider;
    private final RetryTemplate retryTemplate;
    private final CircuitBreaker circuitBreaker;
    
    @Override
    public PaymentResult pay(PaymentRequest request) {
        // 1. 限流检查
        if (!rateLimiter.tryAcquire()) {
            throw new BusinessException("支付接口限流，请稍后重试");
        }
        
        // 2. 熔断检查
        if (circuitBreaker.isOpen()) {
            throw new BusinessException("支付接口暂时不可用，请稍后重试");
        }
        
        // 3. 执行支付（带重试）
        return retryTemplate.execute(context -> {
            try {
                PaymentResult result = targetProvider.pay(request);
                circuitBreaker.recordSuccess();
                return result;
            } catch (Exception e) {
                circuitBreaker.recordFailure();
                throw e;
            }
        });
    }
    
    @Override
    public String getProviderName() {
        return targetProvider.getProviderName();
    }
    
    @Override
    public boolean supports(PaymentMethod paymentMethod) {
        return targetProvider.supports(paymentMethod);
    }
}
```

## 解决的问题

1. **第三方接口差异**：不同支付渠道接口不统一，难以维护
2. **重复的横切逻辑**：重试、限流、熔断逻辑在每个调用处重复
3. **违反开闭原则**：新增支付渠道需要修改大量代码
4. **可测试性差**：直接调用第三方接口难以进行单元测试

## 使用场景

- 多通道短信发送（阿里云、腾讯云、华为云）
- 多种外部支付网关接入（支付宝、微信、银联）
- 多种文件存储服务（OSS、S3、本地存储）
- 多种消息队列（RabbitMQ、Kafka、RocketMQ）

## 完整案例：统一支付网关

### Provider 接口定义

```java
public interface PaymentProvider {
    /**
     * 执行支付
     */
    PaymentResult pay(PaymentRequest request);
    
    /**
     * 查询支付结果
     */
    PaymentResult query(String paymentId);
    
    /**
     * 退款
     */
    RefundResult refund(RefundRequest request);
    
    /**
     * 获取支付渠道名称
     */
    String getProviderName();
    
    /**
     * 是否支持该支付方式
     */
    boolean supports(PaymentMethod paymentMethod);
}
```

### 支付宝适配器

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class AlipayAdapter implements PaymentProvider {
    
    private final AlipayProperties alipayProperties;
    private final AlipayClient alipayClient;
    
    @Override
    public PaymentResult pay(PaymentRequest request) {
        try {
            log.info("支付宝支付开始: orderId={}, amount={}", 
                request.getOrderId(), request.getAmount());
            
            // 1. 构建支付宝请求
            AlipayTradePagePayRequest alipayRequest = new AlipayTradePagePayRequest();
            alipayRequest.setReturnUrl(request.getReturnUrl());
            alipayRequest.setNotifyUrl(request.getNotifyUrl());
            
            AlipayTradePagePayModel model = new AlipayTradePagePayModel();
            model.setOutTradeNo(request.getOrderId());
            model.setTotalAmount(request.getAmount().toString());
            model.setSubject(request.getSubject());
            model.setProductCode("FAST_INSTANT_TRADE_PAY");
            
            alipayRequest.setBizModel(model);
            
            // 2. 调用支付宝SDK
            AlipayTradePagePayResponse response = alipayClient.pageExecute(alipayRequest);
            
            if (response.isSuccess()) {
                PaymentResult result = new PaymentResult();
                result.setSuccess(true);
                result.setPaymentId(request.getOrderId());
                result.setPayUrl(response.getBody());
                result.setProviderName("Alipay");
                return result;
            } else {
                throw new BusinessException("支付宝支付失败: " + response.getSubMsg());
            }
            
        } catch (Exception e) {
            log.error("支付宝支付异常: orderId={}", request.getOrderId(), e);
            throw new BusinessException("支付宝支付异常: " + e.getMessage());
        }
    }
    
    @Override
    public PaymentResult query(String paymentId) {
        try {
            AlipayTradeQueryRequest request = new AlipayTradeQueryRequest();
            AlipayTradeQueryModel model = new AlipayTradeQueryModel();
            model.setOutTradeNo(paymentId);
            request.setBizModel(model);
            
            AlipayTradeQueryResponse response = alipayClient.execute(request);
            
            PaymentResult result = new PaymentResult();
            if (response.isSuccess()) {
                result.setSuccess(true);
                result.setPaymentId(paymentId);
                result.setStatus(convertTradeStatus(response.getTradeStatus()));
            } else {
                result.setSuccess(false);
                result.setErrorMessage(response.getSubMsg());
            }
            return result;
            
        } catch (Exception e) {
            log.error("支付宝查询支付结果异常: paymentId={}", paymentId, e);
            throw new BusinessException("支付宝查询支付结果异常: " + e.getMessage());
        }
    }
    
    @Override
    public RefundResult refund(RefundRequest request) {
        // 退款逻辑
    }
    
    @Override
    public String getProviderName() {
        return "Alipay";
    }
    
    @Override
    public boolean supports(PaymentMethod paymentMethod) {
        return paymentMethod == PaymentMethod.ALIPAY || 
               paymentMethod == PaymentMethod.ALIPAY_H5;
    }
    
    private PaymentStatus convertTradeStatus(String tradeStatus) {
        switch (tradeStatus) {
            case "TRADE_SUCCESS":
            case "TRADE_FINISHED":
                return PaymentStatus.SUCCESS;
            case "WAIT_BUYER_PAY":
                return PaymentStatus.PENDING;
            case "TRADE_CLOSED":
                return PaymentStatus.CLOSED;
            default:
                return PaymentStatus.UNKNOWN;
        }
    }
}
```

### 微信支付适配器

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class WechatPayAdapter implements PaymentProvider {
    
    private final WechatPayProperties wechatPayProperties;
    private final WechatPayClient wechatPayClient;
    
    @Override
    public PaymentResult pay(PaymentRequest request) {
        try {
            log.info("微信支付开始: orderId={}, amount={}", 
                request.getOrderId(), request.getAmount());
            
            // 1. 构建微信支付请求（与支付宝格式不同）
            WechatPayRequest wechatRequest = new WechatPayRequest();
            wechatRequest.setAppid(wechatPayProperties.getAppId());
            wechatRequest.setMchid(wechatPayProperties.getMchId());
            wechatRequest.setDescription(request.getSubject());
            wechatRequest.setOutTradeNo(request.getOrderId());
            wechatRequest.setNotifyUrl(request.getNotifyUrl());
            
            Amount amount = new Amount();
            amount.setTotal(request.getAmount().multiply(new BigDecimal(100)).intValue());
            wechatRequest.setAmount(amount);
            
            // 2. 调用微信支付SDK
            WechatPayResponse response = wechatPayClient.createOrder(wechatRequest);
            
            if (response.isSuccess()) {
                PaymentResult result = new PaymentResult();
                result.setSuccess(true);
                result.setPaymentId(request.getOrderId());
                result.setPayUrl(response.getCodeUrl());
                result.setProviderName("WechatPay");
                return result;
            } else {
                throw new BusinessException("微信支付失败: " + response.getMessage());
            }
            
        } catch (Exception e) {
            log.error("微信支付异常: orderId={}", request.getOrderId(), e);
            throw new BusinessException("微信支付异常: " + e.getMessage());
        }
    }
    
    @Override
    public PaymentResult query(String paymentId) {
        // 查询逻辑（与支付宝格式不同）
    }
    
    @Override
    public RefundResult refund(RefundRequest request) {
        // 退款逻辑（与支付宝格式不同）
    }
    
    @Override
    public String getProviderName() {
        return "WechatPay";
    }
    
    @Override
    public boolean supports(PaymentMethod paymentMethod) {
        return paymentMethod == PaymentMethod.WECHAT || 
               paymentMethod == PaymentMethod.WECHAT_H5;
    }
}
```

### 支付网关（Provider 工厂）

```java
@Component
@RequiredArgsConstructor
public class PaymentGateway {
    
    private final List<PaymentProvider> providers;
    
    /**
     * 获取支持指定支付方式的 Provider
     */
    public PaymentProvider getProvider(PaymentMethod paymentMethod) {
        return providers.stream()
                .filter(provider -> provider.supports(paymentMethod))
                .findFirst()
                .orElseThrow(() -> new BusinessException(
                    "不支持的支付方式: " + paymentMethod));
    }
    
    /**
     * 执行支付（自动选择 Provider）
     */
    public PaymentResult pay(PaymentRequest request) {
        PaymentProvider provider = getProvider(request.getPaymentMethod());
        return provider.pay(request);
    }
    
    /**
     * 查询支付结果
     */
    public PaymentResult query(String paymentId, PaymentMethod paymentMethod) {
        PaymentProvider provider = getProvider(paymentMethod);
        return provider.query(paymentId);
    }
    
    /**
     * 退款
     */
    public RefundResult refund(RefundRequest request) {
        PaymentProvider provider = getProvider(request.getPaymentMethod());
        return provider.refund(request);
    }
}
```

### 带代理的 Provider（增强版）

```java
@Component
@RequiredArgsConstructor
public class EnhancedPaymentProvider implements PaymentProvider {
    
    private final PaymentProvider targetProvider;
    private final RetryTemplate retryTemplate;
    private final RateLimiter rateLimiter;
    private final CircuitBreaker circuitBreaker;
    private final CacheManager cacheManager;
    
    @Override
    public PaymentResult pay(PaymentRequest request) {
        // 1. 限流检查
        if (!rateLimiter.tryAcquire()) {
            throw new BusinessException("支付接口限流，请稍后重试");
        }
        
        // 2. 熔断检查
        if (circuitBreaker.isOpen()) {
            throw new BusinessException("支付接口暂时不可用，请稍后重试");
        }
        
        // 3. 执行支付（带重试）
        return retryTemplate.execute(context -> {
            try {
                PaymentResult result = targetProvider.pay(request);
                circuitBreaker.recordSuccess();
                
                // 4. 缓存支付结果
                cacheManager.put("payment:" + request.getOrderId(), result, 300);
                
                return result;
            } catch (Exception e) {
                circuitBreaker.recordFailure();
                throw e;
            }
        });
    }
    
    @Override
    public PaymentResult query(String paymentId) {
        // 1. 先查缓存
        PaymentResult cached = cacheManager.get("payment:" + paymentId);
        if (cached != null) {
            return cached;
        }
        
        // 2. 调用实际查询
        PaymentResult result = targetProvider.query(paymentId);
        
        // 3. 缓存结果
        if (result != null) {
            cacheManager.put("payment:" + paymentId, result, 300);
        }
        
        return result;
    }
    
    @Override
    public String getProviderName() {
        return targetProvider.getProviderName();
    }
    
    @Override
    public boolean supports(PaymentMethod paymentMethod) {
        return targetProvider.supports(paymentMethod);
    }
}
```

### 使用示例

```java
@Service
@RequiredArgsConstructor
public class OrderPaymentService {
    
    private final PaymentGateway paymentGateway;
    
    /**
     * 创建支付
     */
    public PaymentResult createPayment(Long orderId, PaymentMethod paymentMethod) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        PaymentRequest request = new PaymentRequest();
        request.setOrderId(order.getOrderNo());
        request.setAmount(order.getTotalAmount());
        request.setSubject(order.getSubject());
        request.setPaymentMethod(paymentMethod);
        request.setReturnUrl(getReturnUrl(orderId));
        request.setNotifyUrl(getNotifyUrl());
        
        // 使用统一的 PaymentGateway，自动选择对应的 Provider
        return paymentGateway.pay(request);
    }
    
    /**
     * 查询支付结果
     */
    public PaymentResult queryPayment(String paymentId, PaymentMethod paymentMethod) {
        return paymentGateway.query(paymentId, paymentMethod);
    }
    
    /**
     * 退款
     */
    public RefundResult refund(Long orderId, BigDecimal amount, PaymentMethod paymentMethod) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new BusinessException("订单不存在"));
        
        RefundRequest request = new RefundRequest();
        request.setOrderId(order.getOrderNo());
        request.setPaymentId(order.getPaymentId());
        request.setAmount(amount);
        request.setPaymentMethod(paymentMethod);
        
        return paymentGateway.refund(request);
    }
}
```

## 工程实践要点

### 1. 使用配置类注入不同的 Adapter
```java
@Configuration
public class PaymentProviderConfig {
    
    @Bean
    public PaymentProvider alipayProvider(AlipayAdapter alipayAdapter) {
        // 可以选择是否包装代理
        return new EnhancedPaymentProvider(alipayAdapter, retryTemplate, ...);
    }
    
    @Bean
    public PaymentProvider wechatPayProvider(WechatPayAdapter wechatPayAdapter) {
        return new EnhancedPaymentProvider(wechatPayAdapter, retryTemplate, ...);
    }
}
```

### 2. 支持策略选择
可以根据不同条件选择不同的 Provider：

```java
@Component
public class PaymentProviderSelector {
    
    private final List<PaymentProvider> providers;
    
    public PaymentProvider select(PaymentMethod method, PaymentContext context) {
        // 可以根据金额、地区等因素选择不同的 Provider
        if (context.getAmount().compareTo(new BigDecimal("10000")) > 0) {
            // 大额订单使用更可靠的 Provider
            return providers.stream()
                .filter(p -> p.getProviderName().equals("Alipay"))
                .findFirst()
                .orElse(null);
        }
        
        return providers.stream()
            .filter(p -> p.supports(method))
            .findFirst()
            .orElse(null);
    }
}
```

### 3. 适配器测试
使用 Mock 对象进行单元测试：

```java
@ExtendWith(MockitoExtension.class)
class AlipayAdapterTest {
    
    @Mock
    private AlipayClient alipayClient;
    
    @InjectMocks
    private AlipayAdapter alipayAdapter;
    
    @Test
    void testPay() {
        // Mock 支付宝SDK响应
        AlipayTradePagePayResponse response = new AlipayTradePagePayResponse();
        response.setBody("https://alipay.com/pay/xxx");
        
        when(alipayClient.pageExecute(any())).thenReturn(response);
        
        // 测试
        PaymentRequest request = new PaymentRequest();
        request.setOrderId("ORDER001");
        request.setAmount(new BigDecimal("100"));
        
        PaymentResult result = alipayAdapter.pay(request);
        
        assertTrue(result.isSuccess());
        assertEquals("ORDER001", result.getPaymentId());
    }
}
```

## 与其他模式的组合

### Adapter + Provider + Strategy
根据不同条件选择不同的 Provider：

```java
public interface PaymentProviderStrategy {
    PaymentProvider selectProvider(PaymentMethod method, PaymentContext context);
}

@Component
public class DefaultPaymentProviderStrategy implements PaymentProviderStrategy {
    
    private final List<PaymentProvider> providers;
    
    @Override
    public PaymentProvider selectProvider(PaymentMethod method, PaymentContext context) {
        // 选择策略逻辑
        return providers.stream()
            .filter(p -> p.supports(method))
            .findFirst()
            .orElse(null);
    }
}
```

## 注意事项

1. **异常处理要统一**：不同第三方接口的异常格式不同，需要统一转换
2. **日志要详细**：第三方接口调用失败时，需要详细的日志便于排查
3. **超时设置**：第三方接口调用应该设置合理的超时时间
4. **幂等性**：查询接口应该支持幂等，避免重复查询

## 优势与劣势

### 优势
- ✅ 屏蔽第三方接口差异，统一接口规范
- ✅ 易于扩展，新增支付渠道只需新增 Adapter
- ✅ 横切逻辑（重试、限流）集中管理
- ✅ Adapter 可以独立测试

### 劣势
- ❌ 增加了代码复杂度
- ❌ 需要维护适配逻辑
- ❌ 代理模式可能影响性能（需要考虑缓存优化）

## 适用场景判断

**适合使用 Adapter + Provider 的场景：**
- 需要接入多个第三方服务（支付、短信、存储等）
- 第三方接口格式不统一
- 需要在调用前后增加统一逻辑（重试、限流、熔断）
- 需要支持动态切换第三方服务

**不适合的场景：**
- 只接入一个第三方服务
- 第三方接口格式统一，不需要适配
- 不需要横切逻辑

