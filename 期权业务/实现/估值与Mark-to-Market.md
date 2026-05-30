# 估值与 Mark-to-Market

## 定义

估值（Valuation）是按当前市场参数计算合约公允价值（NPV）的过程；Mark-to-Market（MTM）是每日以市价对持仓进行重估的惯例，是 PnL 与风控的数据来源。

## 原理 / 结构要素

### 估值输入

| 参数 | 来源 | 说明 |
|------|------|------|
| Spot | 市场数据 | 标的当前价格 |
| Vol Surface | 波动率曲面 | 各 Tenor/Strikes 的 IV |
| Discount Curve | 利率曲线 | 无风险贴现 |
| Dividend | 分红预期 | 影响远期价格 |
| Terms | 合约条款 | 结构要素快照 |
| Status | 合约状态 | 敲入/敲出影响 Payoff |

### 估值方法

| 产品 | 方法 |
|------|------|
| 香草 | BSM 解析解 |
| 障碍 | 解析解（连续）/ 蒙特卡洛（离散） |
| 亚式 | 蒙特卡洛 / 近似公式 |
| 雪球/凤凰 | 蒙特卡洛（路径依赖） |

### PnL 分解

```
Daily PnL = Today NPV - Yesterday NPV - CashFlow Today
```

分解维度：Delta PnL、Gamma PnL、Vega PnL、Theta PnL、New Trade PnL。

## 业务规则

1. 日终估值在**生命周期事件处理完成后**执行（先事件、后估值）。
2. 敲入/敲出后立即触发**重算**，不可沿用事件前 NPV。
3. 估值使用当日 `termsVersion` 对应的条款快照。
4. 平仓定价以估值 NPV 为基准（除非双方协商 override）。
5. 估值结果保留 `modelVersion`、`marketDataSnapshotId`，支持审计重跑。

## 工程实现要点

- 批处理：`ValuationBatchJob`，日终 Cron，输入 `valuationDate`。
- 接口：`ValuationService.valuate(contractId, valuationDate, marketData)` → `ValuationResult`。
- 路径依赖产品：蒙特卡洛引擎，配置路径数（如 50,000 paths）。
- Greeks：Bump-and-Revalue 或解析公式，写入 `ValuationResult.greeks`。
- 与生命周期联动：Event Handler 完成后 publish `ValuationTrigger`。
- 存储：`valuation_result` 表，按 contractId + valuationDate 唯一。

## 高频面试点

1. 生命周期事件与估值的时序（先事件后估值）。
2. 敲入后估值模型为何要切换。
3. 雪球用什么方法定价、为什么。
4. Daily PnL 如何分解。
5. 估值结果如何用于平仓定价。
6. 市场数据缺失时日终估值如何处理。

## 待补充项

- 项目中估值引擎名称与 Monte Carlo 路径数配置。
- PnL 分解在系统中的展示方式。
