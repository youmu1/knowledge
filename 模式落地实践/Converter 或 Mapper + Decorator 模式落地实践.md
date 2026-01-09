# Converter / Mapper + Decorator 模式落地实践

## 模式概述

**Converter / Mapper + Decorator** 模式是适配器模式（Adapter Pattern）和装饰器模式（Decorator Pattern）的组合，用于在不同数据对象（Entity、DTO、VO）之间进行转换，并在转换过程中进行数据增强（如翻译ID为名称、格式化数据等）。

## 核心组件

### 1. Converter / Mapper（转换器）
负责纯粹的数据映射，将源对象转换为目标对象。

```java
public interface Converter<S, T> {
    /**
     * 将源对象转换为目标对象
     */
    T convert(S source);
    
    /**
     * 批量转换
     */
    default List<T> convertList(List<S> sources) {
        return sources.stream()
                .map(this::convert)
                .collect(Collectors.toList());
    }
}
```

### 2. Decorator（装饰器）
在转换基础上增加额外的信息填充和数据增强。

```java
public interface DataDecorator<T> {
    /**
     * 装饰目标对象，填充额外信息
     */
    void decorate(T target);
    
    /**
     * 批量装饰
     */
    default void decorateList(List<T> targets) {
        targets.forEach(this::decorate);
    }
}
```

## 解决的问题

1. **数据转换逻辑分散**：将Entity到DTO的转换逻辑集中管理
2. **重复的增强逻辑**：如ID到名称的翻译逻辑在多处重复
3. **转换逻辑难以测试**：转换逻辑分散在Service中，难以独立测试
4. **性能问题**：N+1查询问题（在循环中逐个查询关联数据）

## 使用场景

- Entity 到 DTO/VO 的转换
- 接口返回数据的统一封装
- 数据导出时的格式化
- 不同系统间的数据适配

## 完整案例：订单数据转换与增强

### 基础转换器

```java
@Component
public class OrderEntityToDTOConverter implements Converter<OrderEntity, OrderDTO> {
    
    @Override
    public OrderDTO convert(OrderEntity source) {
        if (source == null) {
            return null;
        }
        
        OrderDTO target = new OrderDTO();
        target.setId(source.getId());
        target.setOrderNo(source.getOrderNo());
        target.setUserId(source.getUserId());
        target.setTotalAmount(source.getTotalAmount());
        target.setStatus(source.getStatus());
        target.setCreateTime(source.getCreateTime());
        
        // 转换订单项
        if (source.getItems() != null) {
            target.setItems(convertOrderItems(source.getItems()));
        }
        
        return target;
    }
    
    private List<OrderItemDTO> convertOrderItems(List<OrderItemEntity> items) {
        return items.stream()
                .map(item -> {
                    OrderItemDTO dto = new OrderItemDTO();
                    dto.setId(item.getId());
                    dto.setProductId(item.getProductId());
                    dto.setProductName(item.getProductName());
                    dto.setQuantity(item.getQuantity());
                    dto.setPrice(item.getPrice());
                    return dto;
                })
                .collect(Collectors.toList());
    }
}
```

### 装饰器：用户信息填充

```java
@Component
@RequiredArgsConstructor
public class UserInfoDecorator implements DataDecorator<OrderDTO> {
    
    private final UserService userService;
    
    @Override
    public void decorate(OrderDTO target) {
        if (target.getUserId() == null) {
            return;
        }
        
        // 批量查询用户信息（避免N+1问题）
        UserDTO user = userService.getById(target.getUserId());
        if (user != null) {
            target.setUserName(user.getName());
            target.setUserPhone(user.getPhone());
            target.setUserAvatar(user.getAvatar());
        }
    }
    
    @Override
    public void decorateList(List<OrderDTO> targets) {
        // 批量获取所有用户ID
        Set<Long> userIds = targets.stream()
                .map(OrderDTO::getUserId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        
        if (userIds.isEmpty()) {
            return;
        }
        
        // 批量查询用户信息
        Map<Long, UserDTO> userMap = userService.getByIds(userIds)
                .stream()
                .collect(Collectors.toMap(UserDTO::getId, Function.identity()));
        
        // 填充用户信息
        targets.forEach(order -> {
            UserDTO user = userMap.get(order.getUserId());
            if (user != null) {
                order.setUserName(user.getName());
                order.setUserPhone(user.getPhone());
                order.setUserAvatar(user.getAvatar());
            }
        });
    }
}
```

### 装饰器：商品信息增强

```java
@Component
@RequiredArgsConstructor
public class ProductInfoDecorator implements DataDecorator<OrderDTO> {
    
    private final ProductService productService;
    
    @Override
    public void decorate(OrderDTO target) {
        if (target.getItems() == null || target.getItems().isEmpty()) {
            return;
        }
        
        // 批量获取所有商品ID
        Set<Long> productIds = target.getItems().stream()
                .map(OrderItemDTO::getProductId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        
        if (productIds.isEmpty()) {
            return;
        }
        
        // 批量查询商品信息
        Map<Long, ProductDTO> productMap = productService.getByIds(productIds)
                .stream()
                .collect(Collectors.toMap(ProductDTO::getId, Function.identity()));
        
        // 填充商品详细信息
        target.getItems().forEach(item -> {
            ProductDTO product = productMap.get(item.getProductId());
            if (product != null) {
                // 如果商品名称不在订单项中，从商品信息获取
                if (StringUtils.isEmpty(item.getProductName())) {
                    item.setProductName(product.getName());
                }
                item.setProductImage(product.getImage());
                item.setProductCategory(product.getCategory());
            }
        });
    }
    
    @Override
    public void decorateList(List<OrderDTO> targets) {
        // 获取所有订单的所有商品ID
        Set<Long> allProductIds = targets.stream()
                .filter(Objects::nonNull)
                .map(OrderDTO::getItems)
                .filter(Objects::nonNull)
                .flatMap(List::stream)
                .map(OrderItemDTO::getProductId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        
        if (allProductIds.isEmpty()) {
            return;
        }
        
        // 批量查询所有商品信息
        Map<Long, ProductDTO> productMap = productService.getByIds(allProductIds)
                .stream()
                .collect(Collectors.toMap(ProductDTO::getId, Function.identity()));
        
        // 为每个订单填充商品信息
        targets.forEach(order -> {
            if (order.getItems() != null) {
                order.getItems().forEach(item -> {
                    ProductDTO product = productMap.get(item.getProductId());
                    if (product != null) {
                        if (StringUtils.isEmpty(item.getProductName())) {
                            item.setProductName(product.getName());
                        }
                        item.setProductImage(product.getImage());
                        item.setProductCategory(product.getCategory());
                    }
                });
            }
        });
    }
}
```

### 装饰器：状态描述翻译

```java
@Component
public class OrderStatusDecorator implements DataDecorator<OrderDTO> {
    
    @Override
    public void decorate(OrderDTO target) {
        if (target.getStatus() != null) {
            target.setStatusDescription(getStatusDescription(target.getStatus()));
        }
    }
    
    private String getStatusDescription(OrderStatus status) {
        switch (status) {
            case PENDING_PAYMENT:
                return "待支付";
            case PAID:
                return "已支付";
            case SHIPPED:
                return "已发货";
            case CONFIRMED:
                return "已确认收货";
            case COMPLETED:
                return "已完成";
            case CANCELLED:
                return "已取消";
            case REFUNDED:
                return "已退款";
            default:
                return "未知状态";
        }
    }
}
```

### 装饰器：金额格式化

```java
@Component
public class AmountFormatDecorator implements DataDecorator<OrderDTO> {
    
    private static final DecimalFormat AMOUNT_FORMAT = new DecimalFormat("#,##0.00");
    
    @Override
    public void decorate(OrderDTO target) {
        if (target.getTotalAmount() != null) {
            target.setTotalAmountFormatted(AMOUNT_FORMAT.format(target.getTotalAmount()));
        }
        
        if (target.getItems() != null) {
            target.getItems().forEach(item -> {
                if (item.getPrice() != null) {
                    item.setPriceFormatted(AMOUNT_FORMAT.format(item.getPrice()));
                }
            });
        }
    }
}
```

### 组合转换服务

```java
@Service
@RequiredArgsConstructor
public class OrderConversionService {
    
    private final OrderEntityToDTOConverter converter;
    private final UserInfoDecorator userInfoDecorator;
    private final ProductInfoDecorator productInfoDecorator;
    private final OrderStatusDecorator statusDecorator;
    private final AmountFormatDecorator amountFormatDecorator;
    
    /**
     * 转换单个订单（完整转换，包含所有装饰）
     */
    public OrderDTO convertFull(OrderEntity source) {
        // 1. 基础转换
        OrderDTO dto = converter.convert(source);
        
        // 2. 依次应用装饰器
        userInfoDecorator.decorate(dto);
        productInfoDecorator.decorate(dto);
        statusDecorator.decorate(dto);
        amountFormatDecorator.decorate(dto);
        
        return dto;
    }
    
    /**
     * 批量转换（优化版，避免N+1查询）
     */
    public List<OrderDTO> convertFullList(List<OrderEntity> sources) {
        // 1. 批量基础转换
        List<OrderDTO> dtos = converter.convertList(sources);
        
        // 2. 批量应用装饰器（使用批量查询优化性能）
        userInfoDecorator.decorateList(dtos);
        productInfoDecorator.decorateList(dtos);
        statusDecorator.decorateList(dtos);
        amountFormatDecorator.decorateList(dtos);
        
        return dtos;
    }
    
    /**
     * 轻量级转换（只转换基础字段，不填充关联信息）
     */
    public OrderDTO convertLight(OrderEntity source) {
        return converter.convert(source);
    }
    
    /**
     * 自定义转换（指定需要应用的装饰器）
     */
    public OrderDTO convertCustom(OrderEntity source, List<DataDecorator<OrderDTO>> decorators) {
        OrderDTO dto = converter.convert(source);
        
        for (DataDecorator<OrderDTO> decorator : decorators) {
            decorator.decorate(dto);
        }
        
        return dto;
    }
}
```

### 使用示例

```java
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {
    
    private final OrderService orderService;
    private final OrderConversionService conversionService;
    
    /**
     * 获取订单详情（完整信息）
     */
    @GetMapping("/{id}")
    public Result<OrderDTO> getOrderDetail(@PathVariable Long id) {
        OrderEntity order = orderService.getById(id);
        OrderDTO dto = conversionService.convertFull(order);
        return Result.success(dto);
    }
    
    /**
     * 获取订单列表（完整信息）
     */
    @GetMapping
    public Result<List<OrderDTO>> getOrderList(OrderQueryRequest request) {
        List<OrderEntity> orders = orderService.list(request);
        
        // 使用批量转换，性能更好
        List<OrderDTO> dtos = conversionService.convertFullList(orders);
        
        return Result.success(dtos);
    }
    
    /**
     * 获取订单列表（轻量级，只包含基础信息）
     */
    @GetMapping("/simple")
    public Result<List<OrderDTO>> getSimpleOrderList(OrderQueryRequest request) {
        List<OrderEntity> orders = orderService.list(request);
        
        // 轻量级转换，不填充关联信息
        List<OrderDTO> dtos = conversionService.convertLightList(orders);
        
        return Result.success(dtos);
    }
}
```

## 工程实践要点

### 1. 使用 MapStruct 简化转换器代码
对于简单的字段映射，可以使用 MapStruct 自动生成：

```java
@Mapper(componentModel = "spring")
public interface OrderEntityToDTOMapper {
    OrderDTO toDTO(OrderEntity entity);
    List<OrderDTO> toDTOList(List<OrderEntity> entities);
}
```

### 2. 批量查询优化性能
装饰器应该支持批量操作，避免N+1查询问题：

```java
// ❌ 不好：逐个查询（N+1问题）
targets.forEach(order -> {
    UserDTO user = userService.getById(order.getUserId());  // N次查询
    order.setUserName(user.getName());
});

// ✅ 好：批量查询
Set<Long> userIds = targets.stream().map(OrderDTO::getUserId).collect(Collectors.toSet());
Map<Long, UserDTO> userMap = userService.getByIds(userIds);  // 1次查询
targets.forEach(order -> {
    UserDTO user = userMap.get(order.getUserId());
    order.setUserName(user.getName());
});
```

### 3. 装饰器链式组合
使用链式组合，让装饰器的应用更灵活：

```java
public class DecoratorChain<T> {
    private final List<DataDecorator<T>> decorators = new ArrayList<>();
    
    public DecoratorChain<T> add(DataDecorator<T> decorator) {
        decorators.add(decorator);
        return this;
    }
    
    public void apply(T target) {
        decorators.forEach(decorator -> decorator.decorate(target));
    }
}

// 使用
DecoratorChain<OrderDTO> chain = new DecoratorChain<OrderDTO>()
    .add(userInfoDecorator)
    .add(productInfoDecorator)
    .add(statusDecorator);
chain.apply(orderDTO);
```

### 4. 缓存装饰结果
对于不经常变化的数据（如状态描述），可以使用缓存：

```java
@Component
public class OrderStatusDecorator implements DataDecorator<OrderDTO> {
    
    private static final Map<OrderStatus, String> STATUS_CACHE = new HashMap<>();
    
    static {
        STATUS_CACHE.put(OrderStatus.PENDING_PAYMENT, "待支付");
        STATUS_CACHE.put(OrderStatus.PAID, "已支付");
        // ...
    }
    
    @Override
    public void decorate(OrderDTO target) {
        if (target.getStatus() != null) {
            target.setStatusDescription(STATUS_CACHE.get(target.getStatus()));
        }
    }
}
```

## 与其他模式的组合

### Converter + Decorator + Strategy
根据不同场景使用不同的装饰器组合：

```java
public enum ConversionStrategy {
    FULL,      // 完整转换，应用所有装饰器
    LIGHT,     // 轻量级转换，只转换基础字段
    DETAIL     // 详情转换，包含详细信息但不包含格式化
}

public class OrderConversionService {
    
    public OrderDTO convert(OrderEntity source, ConversionStrategy strategy) {
        OrderDTO dto = converter.convert(source);
        
        switch (strategy) {
            case FULL:
                applyAllDecorators(dto);
                break;
            case LIGHT:
                // 不应用装饰器
                break;
            case DETAIL:
                applyDetailDecorators(dto);
                break;
        }
        
        return dto;
    }
}
```

## 注意事项

1. **性能优化**：批量转换时一定要使用批量查询，避免N+1问题
2. **空值处理**：转换器和装饰器都要处理好空值情况
3. **循环依赖**：注意装饰器之间的依赖关系，避免循环依赖
4. **数据一致性**：确保装饰器填充的数据与实体数据保持一致

## 优势与劣势

### 优势
- ✅ 转换逻辑集中管理，易于维护
- ✅ 装饰器可复用，可组合
- ✅ 支持批量优化，性能好
- ✅ 转换逻辑可以独立测试

### 劣势
- ❌ 增加了代码复杂度
- ❌ 需要创建较多的转换器和装饰器类
- ❌ 如果装饰器过多，性能可能受影响

## 适用场景判断

**适合使用 Converter + Decorator 的场景：**
- 需要频繁进行 Entity 到 DTO 的转换
- 转换逻辑需要填充关联数据
- 不同接口需要不同级别的数据（完整/简化）
- 需要避免N+1查询问题

**不适合的场景：**
- 简单的字段拷贝（可以使用BeanUtils）
- 转换逻辑非常简单（1-2个字段）

