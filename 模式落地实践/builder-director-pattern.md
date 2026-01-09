# Builder + Director 模式落地实践

## 模式概述

**Builder + Director** 模式是建造者模式（Builder Pattern）的增强版本，通过 Director（指挥者）定义特定的构建逻辑顺序，用于创建复杂的对象，避免构造函数参数过多，提高代码可读性和可维护性。

## 核心组件

### 1. Builder（建造者）
提供流式 API 设置属性，负责构建对象。

```java
public interface Builder<T> {
    /**
     * 构建对象
     */
    T build();
}
```

### 2. Director（指挥者）
定义特定的构建逻辑顺序，封装复杂的构建流程。

```java
public interface Director<T> {
    /**
     * 构建对象
     */
    T construct(Builder<T> builder, BuildContext context);
}
```

### 3. Product（产品）
最终要构建的复杂对象。

## 解决的问题

1. **构造函数参数过多**：超过 5 个参数时，构造函数调用难以理解
2. **可选参数处理**：大量可选参数导致构造函数重载爆炸
3. **构建逻辑复杂**：对象构建需要多步设置，逻辑分散
4. **构建顺序要求**：某些属性需要在其他属性设置后才能设置

## 使用场景

- 构建复杂的查询 Criteria（多条件查询）
- 生成复杂的 Excel 报表定义
- 构建复杂的配置对象（如线程池配置）
- 创建复杂的 API 请求对象

## 完整案例：复杂查询条件构建器

### Builder 定义

```java
public class OrderQueryBuilder implements Builder<OrderQuery> {
    
    private Long userId;
    private OrderStatus status;
    private LocalDate startDate;
    private LocalDate endDate;
    private BigDecimal minAmount;
    private BigDecimal maxAmount;
    private List<PaymentMethod> paymentMethods;
    private List<SortField> sortFields;
    private Integer pageNumber;
    private Integer pageSize;
    
    public OrderQueryBuilder userId(Long userId) {
        this.userId = userId;
        return this;
    }
    
    public OrderQueryBuilder status(OrderStatus status) {
        this.status = status;
        return this;
    }
    
    public OrderQueryBuilder dateRange(LocalDate startDate, LocalDate endDate) {
        this.startDate = startDate;
        this.endDate = endDate;
        return this;
    }
    
    public OrderQueryBuilder amountRange(BigDecimal minAmount, BigDecimal maxAmount) {
        this.minAmount = minAmount;
        this.maxAmount = maxAmount;
        return this;
    }
    
    public OrderQueryBuilder paymentMethods(List<PaymentMethod> paymentMethods) {
        this.paymentMethods = paymentMethods;
        return this;
    }
    
    public OrderQueryBuilder sortBy(List<SortField> sortFields) {
        this.sortFields = sortFields;
        return this;
    }
    
    public OrderQueryBuilder pagination(Integer pageNumber, Integer pageSize) {
        this.pageNumber = pageNumber;
        this.pageSize = pageSize;
        return this;
    }
    
    @Override
    public OrderQuery build() {
        // 验证必填参数
        validate();
        
        // 构建查询对象
        OrderQuery query = new OrderQuery();
        query.setUserId(userId);
        query.setStatus(status);
        query.setStartDate(startDate);
        query.setEndDate(endDate);
        query.setMinAmount(minAmount);
        query.setMaxAmount(maxAmount);
        query.setPaymentMethods(paymentMethods);
        query.setSortFields(sortFields);
        query.setPageNumber(pageNumber != null ? pageNumber : 1);
        query.setPageSize(pageSize != null ? pageSize : 10);
        
        return query;
    }
    
    private void validate() {
        // 验证逻辑
        if (startDate != null && endDate != null && startDate.isAfter(endDate)) {
            throw new IllegalArgumentException("开始日期不能晚于结束日期");
        }
        if (minAmount != null && maxAmount != null && minAmount.compareTo(maxAmount) > 0) {
            throw new IllegalArgumentException("最小金额不能大于最大金额");
        }
    }
}
```

### Director 定义

```java
public interface OrderQueryDirector {
    /**
     * 构建默认查询（按照默认规则）
     */
    OrderQuery constructDefault(Builder<OrderQuery> builder, BuildContext context);
    
    /**
     * 构建时间范围查询（先设置时间范围，再设置其他条件）
     */
    OrderQuery constructDateRangeQuery(Builder<OrderQuery> builder, BuildContext context);
    
    /**
     * 构建金额范围查询（先设置金额范围，再设置其他条件）
     */
    OrderQuery constructAmountRangeQuery(Builder<OrderQuery> builder, BuildContext context);
}
```

### Director 实现

```java
@Component
@RequiredArgsConstructor
public class OrderQueryDirectorImpl implements OrderQueryDirector {
    
    private final UserService userService;
    
    @Override
    public OrderQuery constructDefault(OrderQueryBuilder builder, BuildContext context) {
        // 1. 设置用户ID（如果未指定，使用当前用户）
        Long userId = context.getUserId();
        if (userId == null) {
            userId = getCurrentUserId();
        }
        builder.userId(userId);
        
        // 2. 设置分页（默认第一页，每页10条）
        builder.pagination(1, 10);
        
        // 3. 设置排序（默认按创建时间倒序）
        builder.sortBy(Arrays.asList(
            new SortField("createTime", SortDirection.DESC)
        ));
        
        // 4. 设置时间范围（如果指定）
        if (context.getStartDate() != null && context.getEndDate() != null) {
            builder.dateRange(context.getStartDate(), context.getEndDate());
        }
        
        // 5. 设置状态（如果指定）
        if (context.getStatus() != null) {
            builder.status(context.getStatus());
        }
        
        return builder.build();
    }
    
    @Override
    public OrderQuery constructDateRangeQuery(OrderQueryBuilder builder, BuildContext context) {
        // 1. 先设置时间范围（必须）
        if (context.getStartDate() == null || context.getEndDate() == null) {
            throw new IllegalArgumentException("时间范围查询必须指定开始和结束日期");
        }
        builder.dateRange(context.getStartDate(), context.getEndDate());
        
        // 2. 设置用户ID
        Long userId = context.getUserId();
        if (userId == null) {
            userId = getCurrentUserId();
        }
        builder.userId(userId);
        
        // 3. 设置状态（可选）
        if (context.getStatus() != null) {
            builder.status(context.getStatus());
        }
        
        // 4. 设置分页
        builder.pagination(
            context.getPageNumber() != null ? context.getPageNumber() : 1,
            context.getPageSize() != null ? context.getPageSize() : 10
        );
        
        // 5. 设置排序（默认按创建时间倒序）
        builder.sortBy(Arrays.asList(
            new SortField("createTime", SortDirection.DESC)
        ));
        
        return builder.build();
    }
    
    @Override
    public OrderQuery constructAmountRangeQuery(OrderQueryBuilder builder, BuildContext context) {
        // 1. 先设置金额范围（必须）
        if (context.getMinAmount() == null || context.getMaxAmount() == null) {
            throw new IllegalArgumentException("金额范围查询必须指定最小和最大金额");
        }
        builder.amountRange(context.getMinAmount(), context.getMaxAmount());
        
        // 2. 设置用户ID
        Long userId = context.getUserId();
        if (userId == null) {
            userId = getCurrentUserId();
        }
        builder.userId(userId);
        
        // 3. 设置状态（可选）
        if (context.getStatus() != null) {
            builder.status(context.getStatus());
        }
        
        // 4. 设置时间范围（可选）
        if (context.getStartDate() != null && context.getEndDate() != null) {
            builder.dateRange(context.getStartDate(), context.getEndDate());
        }
        
        // 5. 设置分页
        builder.pagination(
            context.getPageNumber() != null ? context.getPageNumber() : 1,
            context.getPageSize() != null ? context.getPageSize() : 10
        );
        
        // 6. 设置排序（按金额倒序）
        builder.sortBy(Arrays.asList(
            new SortField("totalAmount", SortDirection.DESC)
        ));
        
        return builder.build();
    }
    
    private Long getCurrentUserId() {
        // 获取当前登录用户ID
        return userService.getCurrentUserId();
    }
}
```

### BuildContext（构建上下文）

```java
public class BuildContext {
    private Long userId;
    private OrderStatus status;
    private LocalDate startDate;
    private LocalDate endDate;
    private BigDecimal minAmount;
    private BigDecimal maxAmount;
    private Integer pageNumber;
    private Integer pageSize;
    
    public static BuildContext of() {
        return new BuildContext();
    }
    
    public BuildContext userId(Long userId) {
        this.userId = userId;
        return this;
    }
    
    public BuildContext status(OrderStatus status) {
        this.status = status;
        return this;
    }
    
    public BuildContext dateRange(LocalDate startDate, LocalDate endDate) {
        this.startDate = startDate;
        this.endDate = endDate;
        return this;
    }
    
    public BuildContext amountRange(BigDecimal minAmount, BigDecimal maxAmount) {
        this.minAmount = minAmount;
        this.maxAmount = maxAmount;
        return this;
    }
    
    public BuildContext pagination(Integer pageNumber, Integer pageSize) {
        this.pageNumber = pageNumber;
        this.pageSize = pageSize;
        return this;
    }
    
    // getters
}
```

### 使用示例

#### 方式一：直接使用 Builder（简单场景）

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    
    /**
     * 简单查询（直接使用 Builder）
     */
    public List<Order> queryOrders(Long userId, OrderStatus status) {
        OrderQuery query = new OrderQueryBuilder()
            .userId(userId)
            .status(status)
            .pagination(1, 10)
            .sortBy(Arrays.asList(new SortField("createTime", SortDirection.DESC)))
            .build();
        
        return orderRepository.query(query);
    }
}
```

#### 方式二：使用 Director（复杂场景）

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    
    private final OrderQueryDirector queryDirector;
    
    /**
     * 默认查询（使用 Director）
     */
    public List<Order> queryOrdersDefault() {
        BuildContext context = BuildContext.of();
        
        OrderQuery query = queryDirector.constructDefault(
            new OrderQueryBuilder(),
            context
        );
        
        return orderRepository.query(query);
    }
    
    /**
     * 时间范围查询（使用 Director）
     */
    public List<Order> queryOrdersByDateRange(LocalDate startDate, LocalDate endDate) {
        BuildContext context = BuildContext.of()
            .dateRange(startDate, endDate)
            .status(OrderStatus.PAID)
            .pagination(1, 20);
        
        OrderQuery query = queryDirector.constructDateRangeQuery(
            new OrderQueryBuilder(),
            context
        );
        
        return orderRepository.query(query);
    }
    
    /**
     * 金额范围查询（使用 Director）
     */
    public List<Order> queryOrdersByAmountRange(BigDecimal minAmount, BigDecimal maxAmount) {
        BuildContext context = BuildContext.of()
            .amountRange(minAmount, maxAmount)
            .status(OrderStatus.COMPLETED)
            .pagination(1, 50);
        
        OrderQuery query = queryDirector.constructAmountRangeQuery(
            new OrderQueryBuilder(),
            context
        );
        
        return orderRepository.query(query);
    }
}
```

## 完整案例：Excel 报表定义构建器

### Excel 报表定义 Builder

```java
public class ExcelReportDefinitionBuilder implements Builder<ExcelReportDefinition> {
    
    private String sheetName;
    private List<ExcelColumn> columns = new ArrayList<>();
    private ExcelStyle headerStyle;
    private ExcelStyle dataStyle;
    private List<ExcelFilter> filters = new ArrayList<>();
    private ExcelExportConfig exportConfig;
    
    public ExcelReportDefinitionBuilder sheetName(String sheetName) {
        this.sheetName = sheetName;
        return this;
    }
    
    public ExcelReportDefinitionBuilder addColumn(ExcelColumn column) {
        this.columns.add(column);
        return this;
    }
    
    public ExcelReportDefinitionBuilder addColumns(List<ExcelColumn> columns) {
        this.columns.addAll(columns);
        return this;
    }
    
    public ExcelReportDefinitionBuilder headerStyle(ExcelStyle style) {
        this.headerStyle = style;
        return this;
    }
    
    public ExcelReportDefinitionBuilder dataStyle(ExcelStyle style) {
        this.dataStyle = style;
        return this;
    }
    
    public ExcelReportDefinitionBuilder addFilter(ExcelFilter filter) {
        this.filters.add(filter);
        return this;
    }
    
    public ExcelReportDefinitionBuilder exportConfig(ExcelExportConfig config) {
        this.exportConfig = config;
        return this;
    }
    
    @Override
    public ExcelReportDefinition build() {
        validate();
        
        ExcelReportDefinition definition = new ExcelReportDefinition();
        definition.setSheetName(sheetName != null ? sheetName : "Sheet1");
        definition.setColumns(columns);
        definition.setHeaderStyle(headerStyle != null ? headerStyle : getDefaultHeaderStyle());
        definition.setDataStyle(dataStyle != null ? dataStyle : getDefaultDataStyle());
        definition.setFilters(filters);
        definition.setExportConfig(exportConfig != null ? exportConfig : getDefaultExportConfig());
        
        return definition;
    }
    
    private void validate() {
        if (columns.isEmpty()) {
            throw new IllegalArgumentException("报表至少需要一列");
        }
    }
    
    private ExcelStyle getDefaultHeaderStyle() {
        // 默认样式
    }
    
    private ExcelStyle getDefaultDataStyle() {
        // 默认样式
    }
    
    private ExcelExportConfig getDefaultExportConfig() {
        // 默认配置
    }
}
```

### Excel 报表 Director

```java
@Component
public class OrderReportDirector {
    
    /**
     * 构建订单明细报表定义
     */
    public ExcelReportDefinition constructOrderDetailReport(ExcelReportDefinitionBuilder builder) {
        return builder
            .sheetName("订单明细")
            .addColumn(new ExcelColumn("订单号", "orderNo", 200))
            .addColumn(new ExcelColumn("用户姓名", "userName", 150))
            .addColumn(new ExcelColumn("订单金额", "totalAmount", 120, 
                value -> new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP).toString()))
            .addColumn(new ExcelColumn("订单状态", "status", 100, this::formatStatus))
            .addColumn(new ExcelColumn("创建时间", "createTime", 180, 
                value -> LocalDateTime.parse(value.toString()).format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))))
            .addColumn(new ExcelColumn("支付时间", "paymentTime", 180, 
                value -> value != null ? LocalDateTime.parse(value.toString()).format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) : ""))
            .headerStyle(createBoldHeaderStyle())
            .dataStyle(createDefaultDataStyle())
            .exportConfig(ExcelExportConfig.builder()
                .includeHeader(true)
                .autoSizeColumns(true)
                .build())
            .build();
    }
    
    /**
     * 构建订单统计报表定义
     */
    public ExcelReportDefinition constructOrderStatisticsReport(ExcelReportDefinitionBuilder builder) {
        return builder
            .sheetName("订单统计")
            .addColumn(new ExcelColumn("日期", "date", 120))
            .addColumn(new ExcelColumn("订单数量", "orderCount", 120))
            .addColumn(new ExcelColumn("订单金额", "orderAmount", 120,
                value -> new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP).toString()))
            .addColumn(new ExcelColumn("平均订单金额", "avgOrderAmount", 120,
                value -> new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP).toString()))
            .headerStyle(createBoldHeaderStyle())
            .dataStyle(createDefaultDataStyle())
            .exportConfig(ExcelExportConfig.builder()
                .includeHeader(true)
                .autoSizeColumns(true)
                .build())
            .build();
    }
    
    private String formatStatus(Object status) {
        if (status == null) {
            return "";
        }
        OrderStatus orderStatus = OrderStatus.valueOf(status.toString());
        switch (orderStatus) {
            case PENDING_PAYMENT:
                return "待支付";
            case PAID:
                return "已支付";
            case SHIPPED:
                return "已发货";
            case COMPLETED:
                return "已完成";
            default:
                return status.toString();
        }
    }
    
    private ExcelStyle createBoldHeaderStyle() {
        // 创建粗体表头样式
    }
    
    private ExcelStyle createDefaultDataStyle() {
        // 创建默认数据样式
    }
}
```

## 工程实践要点

### 1. Builder 应该支持链式调用
所有设置方法都应该返回 Builder 自身，支持链式调用：

```java
public class OrderQueryBuilder {
    public OrderQueryBuilder userId(Long userId) {
        this.userId = userId;
        return this;  // 返回自身，支持链式调用
    }
    
    public OrderQueryBuilder status(OrderStatus status) {
        this.status = status;
        return this;
    }
}
```

### 2. Builder 应该在 build() 时验证
在 `build()` 方法中进行参数验证，而不是在设置时验证：

```java
@Override
public OrderQuery build() {
    validate();  // 构建时验证
    // ...
}

private void validate() {
    if (startDate != null && endDate != null && startDate.isAfter(endDate)) {
        throw new IllegalArgumentException("开始日期不能晚于结束日期");
    }
}
```

### 3. Director 应该封装构建顺序
Director 负责定义构建的顺序和规则，隐藏复杂的构建逻辑：

```java
public OrderQuery constructDateRangeQuery(Builder builder, BuildContext context) {
    // 1. 先设置必填参数（时间范围）
    builder.dateRange(context.getStartDate(), context.getEndDate());
    
    // 2. 再设置可选参数
    if (context.getStatus() != null) {
        builder.status(context.getStatus());
    }
    
    // 3. 最后设置默认值
    builder.pagination(1, 10);
    
    return builder.build();
}
```

### 4. 支持部分构建
支持只设置部分参数，其他使用默认值：

```java
public OrderQuery build() {
    // 使用默认值
    if (pageNumber == null) {
        pageNumber = 1;
    }
    if (pageSize == null) {
        pageSize = 10;
    }
    // ...
}
```

## 与其他模式的组合

### Builder + Director + Strategy
根据不同策略使用不同的 Director：

```java
public interface ReportDirectorStrategy {
    ExcelReportDefinition constructReport(ExcelReportDefinitionBuilder builder);
}

@Component
public class OrderDetailReportStrategy implements ReportDirectorStrategy {
    @Override
    public ExcelReportDefinition constructReport(ExcelReportDefinitionBuilder builder) {
        // 订单明细报表构建逻辑
    }
}

@Component
public class OrderStatisticsReportStrategy implements ReportDirectorStrategy {
    @Override
    public ExcelReportDefinition constructReport(ExcelReportDefinitionBuilder builder) {
        // 订单统计报表构建逻辑
    }
}
```

## 注意事项

1. **Builder 应该是线程不安全的**：每个线程应该创建自己的 Builder 实例
2. **build() 应该是幂等的**：可以多次调用 build()，每次都返回新的对象
3. **参数验证应该在 build() 时进行**：而不是在设置时验证
4. **Director 应该封装构建顺序**：隐藏复杂的构建逻辑

## 优势与劣势

### 优势
- ✅ 避免构造函数参数过多
- ✅ 支持可选参数
- ✅ 构建逻辑清晰
- ✅ Director 可以封装复杂的构建顺序

### 劣势
- ❌ 增加了代码复杂度
- ❌ 需要创建较多的类
- ❌ 如果对象构建很简单，使用 Builder 是过度设计

## 适用场景判断

**适合使用 Builder + Director 的场景：**
- 对象有很多可选参数（>5个）
- 构建对象需要多步设置，有顺序要求
- 需要支持多种构建方式（不同的 Director）
- 对象构建逻辑复杂

**不适合的场景：**
- 对象参数很少（<3个）
- 所有参数都是必填的
- 构建逻辑非常简单

