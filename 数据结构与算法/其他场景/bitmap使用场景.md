# Bitmap 使用场景

## 定义

Bitmap（位图）是用 **连续 bit 位** 表示元素「存在 / 不存在」或「是 / 否」状态的数据结构。每个元素映射到一个固定整数下标，对应数组中的一个 bit：1 表示存在/真，0 表示不存在/假。

与 `HashSet` 等通用集合不同，Bitmap 不存储元素本身，只存储 **membership（成员关系）**，因此空间占用与 **值域上界** 相关，与 **实际元素个数** 无关。

常见实现：

| 实现 | 说明 |
|------|------|
| Java `BitSet` | JDK 内置，底层 `long[]`，支持动态扩容 |
| Redis Bitmap | 基于 String 的 bit 操作命令（`SETBIT`/`GETBIT`/`BITCOUNT`/`BITOP`） |
| RoaringBitmap | 稀疏场景优化，分段压缩存储 |
| 手写 `byte[]` / `long[]` | 算法题或极致性能场景 |

## 原理

### 映射规则

1. 元素必须是 **非负整数 ID** 或可映射为 `[0, N)` 范围内的整数。
2. 元素 `id` 映射到第 `id` 个 bit：
   - 数组下标：`index = id / 8`（按 byte）或 `id / 64`（按 long）
   - 位偏移：`offset = id % 8` 或 `id % 64`
3. 操作均通过 **位运算** 完成，单次置位/清位/判位时间复杂度 O(1)。

### 位运算操作

| 操作 | 含义 | 表达式（以 bit 在 byte 内为例） |
|------|------|--------------------------------|
| 置位（set） | 标记存在 | `arr[i] \|= (1 << offset)` |
| 清位（clear） | 标记不存在 | `arr[i] &= ~(1 << offset)` |
| 判位（test） | 查询是否存在 | `(arr[i] & (1 << offset)) != 0` |
| 翻转（flip） | 切换状态 | `arr[i] ^= (1 << offset)` |

### 集合运算

多个 Bitmap 长度一致时，可用位运算做集合操作（每一位独立运算）：

| 集合操作 | 位运算 |
|----------|--------|
| 并集 | `\|` |
| 交集 | `&` |
| 差集 | `& ~` |
| 对称差 | `^` |

Redis 中对应 `BITOP AND` / `OR` / `XOR` / `NOT`。

### 空间与复杂度

| 指标 | Bitmap | HashSet（存 Integer） |
|------|--------|----------------------|
| 空间 | `N / 8` 字节（覆盖值域 `[0, N)`） | 约 `元素数 × (对象头 + Integer 开销)`，JDK 下每个 Integer 约 16B+ |
| 置位 / 查位 | O(1) | 平均 O(1)，有 hash 与 boxing 开销 |
| 适用条件 | ID 密集、值域有界 | ID 稀疏、值域大或元素非整数 |

**空间对比示例**：值域 `[0, 10^8)`，即 1 亿个可能 ID。

- Bitmap：`10^8 / 8 ≈ 12.5 MB`（固定）
- HashSet 存 100 万个 ID：约 `10^6 × 32B ≈ 32 MB`（随元素数增长）

规则：当 **值域上界较小且 ID 密集** 时 Bitmap 更省空间；当 **实际元素远小于值域**（稀疏）时，固定大小的 Bitmap 浪费严重，需 RoaringBitmap 或 HashSet。

### 三条核心设计原则

1. **用值域换空间**：以 `[0, N)` 全覆盖的 bit 数组，换取 O(1) 判重与集合运算。
2. **只存状态不存值**：适合「是否签到」「是否活跃」「是否在黑名单」等布尔语义。
3. **稀疏数据需压缩**：超大稀疏 ID 空间不能直接用单块 Bitmap，需分段或 RoaringBitmap。

## 应用场景

| 场景 | 用法 | 选型理由 |
|------|------|----------|
| 用户签到 | 用户 ID 映射到「第几天」的 bit | 365 天只需 365 bit/用户；或按天一个 Bitmap，每位代表一个用户 |
| DAU / 活跃判定 | 当天活跃用户在 Bitmap 中置位 | O(1) 判活，便于与其他天做交并集 |
| UV 统计（精确） | 每个独立访客 ID 对应一个 bit | 值域可控时精确去重；值域极大时用 HyperLogLog 近似 |
| 黑白名单 | 用户 ID 置位表示封禁/放行 | 判位 O(1)，内存远小于 HashSet |
| 海量 ID 去重 | 导入流水时逐位置位，已置位则重复 | 比 HashSet 省空间（密集 ID 场景） |
| 权限掩码 | 多个权限用一个 int/long 的各位表示 | 系统级 Bitmap，与集合 Bitmap 同一原理 |
| 布隆过滤器（相关） | 多个 hash 映射到 bit 数组 | 允许假阳性、不允许假阴性；空间比 HashSet 更小但有误判 |
| 倒排索引过滤 | 文档/标签集合用 Bitmap 交并集 | 搜索引擎中快速求「同时含 A 和 B 标签」的文档 |

### 两种常见建模方式

1. **按实体分 Bitmap**：每个用户一个 Bitmap，每位代表某一天是否签到。适合查「某用户某月签到情况」。
2. **按维度分 Bitmap**：每天一个 Bitmap，每位代表一个用户 ID。适合查「某天签到人数（BITCOUNT）」和「连续 N 天都签到的用户（BITOP AND）」。

## 高频面试点

1. **Bitmap 与 HashSet 的空间对比**：值域有界且密集时 Bitmap 更优；稀疏或值域极大时 HashSet 或 RoaringBitmap 更优。
2. **适用数据范围与限制**：元素必须可映射为非负整数；值域上界决定内存下限；不支持直接存字符串（需 hash，有碰撞风险）。
3. **位运算操作**：置位、清位、判位、翻转及交并差。
4. **Redis Bitmap 命令**：`SETBIT`、`GETBIT`、`BITCOUNT`、`BITOP` 的工程落地。
5. **与 Bloom Filter 的区别**：Bitmap 精确无假阳性（值域内）；Bloom Filter 省空间但有假阳性。
6. **稀疏优化**：RoaringBitmap 分段（array / bitmap / run 编码）。

## 面试官视角：Bitmap 考题设计

### 考察规则

1. **基础题**考察概念边界，要求候选人能说明 Bitmap 存什么、不存什么、与 HashSet 的差异。
2. **原理题**考察位运算与复杂度，要求候选人能手写置位/判位及空间估算。
3. **选型题**考察工程取舍，要求候选人能根据 ID 密度、值域大小、精确/近似需求选择方案。
4. **落地题**考察 Redis / Java 实现，要求候选人能说明 key 设计、内存估算和 BITOP 用法。
5. **优化题**考察稀疏场景，要求候选人能提出 RoaringBitmap、分段 Bitmap 或 HyperLogLog。

### 基础理解题

1. **Bitmap 是什么？解决什么问题？**
   - 考察点：是否理解「用 bit 表示 membership」而非存储元素本身。
   - 追问方向：Bitmap 能否存储用户 ID 列表并原样遍历？
   - 参考回答：Bitmap 用连续 bit 表示某个整数 ID 是否存在。它解决大规模布尔标记、快速判重和集合交并集问题。它不能原样遍历出所有 ID 列表（需扫描全部 bit，O(N)），也不存储 ID 以外的属性；若需存附加信息，应配合 HashMap 或数据库。

2. **Bitmap 与 HashSet 的区别？何时选 Bitmap？**
   - 考察点：空间模型、值域 vs 元素数、O(1) 操作语义。
   - 追问方向：100 万个用户 ID，值域 `[0, 10^9)`，选哪个？
   - 参考回答：HashSet 空间与元素个数成正比，适合稀疏、值域大的场景。Bitmap 空间与值域上界成正比，适合 ID 密集且值域有界的场景。值域 10^9 时 Bitmap 需约 125 MB 固定开销，若实际只有 100 万元素则浪费严重，应选 HashSet 或 RoaringBitmap。

3. **Bitmap 与 Bloom Filter 的区别？**
   - 考察点：精确 vs 近似、假阳性、使用场景。
   - 追问方向：缓存穿透防护用哪个？
   - 参考回答：Bitmap 在值域 `[0, N)` 内精确表示 membership，无假阳性。Bloom Filter 用多个 hash 映射到 bit 数组，空间更小但存在假阳性（可能误判存在），不存在假阴性。缓存穿透「判断 key 是否可能存在」常用 Bloom Filter；已知整数 ID 且需精确去重用 Bitmap 或 HashSet。

### 原理与手写题

1. **如何用 `byte[]` 实现 set / test 操作？**
   - 考察点：index 与 offset 计算、位运算正确性。
   - 追问方向：如果 ID 从 1 开始而非 0，如何处理？
   - 参考回答：`set(id)`：`arr[id/8] |= (1 << (id%8))`。`test(id)`：`(arr[id/8] & (1 << (id%8))) != 0`。ID 从 1 开始时，映射时用 `id-1` 作为 bit 下标，或分配 `N+1` 长度并忽略第 0 位。注意 `1 << 7` 在 byte 中符号扩展问题，Java 中应对 `byte` 先 `& 0xFF` 或使用 `BitSet`。

2. **两个 Bitmap 求交集表示什么？时间复杂度？**
   - 考察点：按位与的集合语义与线性扫描成本。
   - 追问方向：1000 万 bit 的 Bitmap 做 AND，如何估算耗时？
   - 参考回答：交集表示同时存在于两个集合中的 ID。对每个 word（如 long）做 `&` 即可，复杂度 O(N/w)，N 为 bit 总数，w 为字长。1000 万 bit ≈ 1.25 MB，现代 CPU 毫秒级可完成；Redis `BITOP AND` 同理。

3. **如何统计 Bitmap 中 1 的个数（popcount）？**
   - 考察点：是否知道 `BITCOUNT`、Brian Kernighan 算法、CPU 指令。
   - 参考回答：逐 byte 统计：Java `BitSet.cardinality()`、Redis `BITCOUNT`。高效实现可用 CPU popcount 指令（`Long.bitCount`）或 Brian Kernighan：`n & (n-1)` 清除最低位 1，循环计数。

### 场景设计题

1. **设计一个用户签到系统，支持查询某用户本月签到天数和某天签到总人数。**
   - 考察点：两种建模方式的选型与 Redis key 设计。
   - 追问方向：用户量 1 亿，如何估算内存？
   - 参考回答：按天建 Bitmap：`sign:20250530`，用户 ID 为 bit 偏移，`SETBIT` 签到，`BITCOUNT` 得当天人数。查某用户本月签到：取 30 个 daily Bitmap，对该用户 ID 逐天 `GETBIT` 累加；或对用户建月 Bitmap（31 bit）。1 亿用户每天一个 Bitmap 约 `10^8/8 ≈ 12.5 MB`，30 天约 375 MB，需评估 Redis 内存与过期策略。

2. **海量日志中的 userId 去重，userId 范围 `[0, 5000万)`，约 1 亿条记录，如何设计？**
   - 考察点：Bitmap 精确去重 vs 流式处理。
   - 追问方向：单机内存不够怎么办？
   - 参考回答：userId 值域 5000 万，Bitmap 约 `5000万/8 ≈ 6.25 MB`，单机可承受。遍历日志，对每个 userId 若 `test` 为 false 则 `set` 并计数。内存不够时可分片：按 `userId % 分片数` 分到多个 Bitmap 或多台机器，最后汇总 `BITCOUNT` 之和（注意跨分片无重复，因 userId 唯一映射）。

3. **判断用户是否在黑名单，QPS 10 万，如何设计？**
   - 考察点：Bitmap O(1) 查询、本地缓存 vs Redis、热 key。
   - 参考回答：黑名单 userId 映射为 Bitmap，判位 O(1)。QPS 10 万时优先本地内存 Bitmap（或分片加载），Redis 作为数据源定期同步；或 Redis Bitmap + 本地 Bloom Filter 前置过滤（允许少量假阳性时再查 Redis）。需明确黑名单 ID 值域，估算 Bitmap 大小。

### Redis 落地题

1. **Redis Bitmap 底层是什么？`SETBIT key offset value` 的复杂度？**
   - 考察点：是否理解 Redis String 的 SDS 可扩展为 bit 数组。
   - 追问方向：`offset` 最大多少？
   - 参考回答：Redis Bitmap 不是独立类型，是对 String 值的 bit 操作。`SETBIT` 会扩展 String 到能容纳 offset 的长度，O(1) 均摊。Redis 规定 offset 上限 `2^32 - 1`（约 512 MB bit 空间）。`BITCOUNT` 时间 O(N)，N 为字符串字节长度。

2. **如何用 Redis 统计 3 天内连续签到的用户？**
   - 考察点：`BITOP AND` 跨 key 集合运算。
   - 参考回答：维护 `sign:day1`、`sign:day2`、`sign:day3` 三个 Bitmap。`BITOP AND sign:3days sign:day1 sign:day2 sign:day3` 得到三天都签到的用户 Bitmap，`BITCOUNT sign:3days` 得人数。查某用户是否连续签到：`GETBIT sign:3days userId`。

3. **Redis Bitmap 和 Set 存 userId 列表，如何选型？**
   - 考察点：内存估算、元素稀疏度、是否需要列出全部成员。
   - 参考回答：值域 `[0, N)` 且 N 不太大、只需判存在或计数时用 Bitmap，内存 `N/8` 字节。元素稀疏、值域极大、或需 `SMEMBERS` 列出全部时用 Set。经验：元素数 < 值域的 1/10 且值域 > 百万时，Set 往往更省内存。

### 稀疏与优化题

1. **超大范围稀疏 ID（如 `[0, 2^32)`，实际只有 10 万元素）如何优化？**
   - 考察点：RoaringBitmap、分段 Bitmap、HashSet 选型。
   - 追问方向：RoaringBitmap 的分段策略是什么？
   - 参考回答：全量 Bitmap 需 512 MB，不可接受。可选：① HashSet，空间与 10 万元素成正比；② 分段 Bitmap，按高 16 位分 65536 段，仅分配有数据段；③ RoaringBitmap，将 32 位 ID 分为高 16 位容器索引 + 低 16 位，容器按密度选择 array / bitmap / run 编码，稀疏时极省空间且支持高效交并集。工程上推荐 RoaringBitmap（Java 库 `org.roaringbitmap`）。

2. **RoaringBitmap 为什么比原生 Bitmap 适合稀疏数据？**
   - 考察点：容器分治、三种编码自适应。
   - 参考回答：RoaringBitmap 将 ID 按高 16 位分成 65536 个容器，每个容器内仅 65536 个可能值。容器内根据密度选择：元素少时用 sorted array；密集时用 bitmap；连续区间用 run 编码。稀疏时大部分容器为空不占空间，密集段仍保持 O(1) 判位和高效位运算。

### 算法建模题

1. **找出两个超大整数数组中的公共元素（ID 范围 `[0, 10^7)`）。**
   - 考察点：Bitmap 做交集标记。
   - 参考回答：遍历数组 A，对 `set(id)`。遍历数组 B，`test(id)` 为 true 则加入结果。时间 O(m+n)，空间 `10^7/8 ≈ 1.25 MB`，优于 HashSet 的双重 hash 开销（值域小时）。

2. **权限系统：用户拥有多个角色，每个角色有多个权限，如何判断用户是否有某权限？**
   - 考察点：bit mask 思想。
   - 参考回答：每个权限分配一个 bit 位（如 `READ=1<<0, WRITE=1<<1`）。角色权限 = 多个 bit 的或。用户权限 = 所属角色权限的或。判断：` (userPerm & targetPerm) == targetPerm `，O(1)。权限数超过 64 时用 `BitSet` 或 `long[]`。

## 延伸问题

1. **超大范围稀疏数据如何优化（分段 Bitmap / RoaringBitmap）？**
   - 参考回答：见上文「稀疏与优化题」。核心规则：稀疏用 HashSet 或 RoaringBitmap；分段按高位切分，仅分配非空段；RoaringBitmap 是工业标准稀疏 Bitmap 实现。

2. **如何与 Redis Bitmap 能力结合落地？**
   - 参考回答：key 按业务维度设计（如 `sign:{date}`、`blacklist:global`）；用 `SETBIT/GETBIT` 读写，`BITCOUNT` 统计，`BITOP` 做跨天/跨条件集合运算；设置 TTL 控制历史数据内存；超大 key 监控 `MEMORY USAGE`；只读场景可本地缓存整段 Bitmap 或布隆前置。

3. **Bitmap 有哪些不适用的情况？**
   - 参考回答：① 元素无法映射为有界非负整数；② 值域极大且稀疏（内存浪费）；③ 需要存储附加属性（仅 membership 不够）；④ 需要有序遍历输出（Bitmap 只能扫描全值域）；⑤ 需要删除大量元素且值域不变（清位可以，但空间不回收，RoaringBitmap 可压缩）。

4. **Java `BitSet` 与手写 `byte[]` 的差异？**
   - 参考回答：`BitSet` 底层 `long[]`，自动扩容、线程不安全、提供 `cardinality`、`nextSetBit` 等 API。手写 `byte[]` 更轻量可控，适合算法题固定值域。`BitSet` 的 `size()` 返回最高置位 + 1，不是 bit 为 1 的个数。

5. **HyperLogLog 与 Bitmap 在 UV 统计上的取舍？**
   - 参考回答：Bitmap 精确，内存与值域上界成正比，适合独立访客 ID 值域有界（如 `[0, 10^8)` 约 12.5 MB）。HyperLogLog 近似，标准误差约 0.81%，固定约 12 KB，适合 UV 极大、可接受约 1% 误差的场景。Redis 提供 `PFADD`/`PFCOUNT`。

## 回答策略（候选人视角）

1. **先给适用条件**：ID 可映射整数、值域有界、密集或需集合运算。
2. **算空间**：`N bit = N/8 字节`，与元素个数无关，这是与 HashSet 对比的关键。
3. **写核心操作**：置位、判位、BITCOUNT、BITOP AND/OR。
4. **主动说边界**：稀疏不适用、不能存附加信息、不能处理非整数 ID（除非 hash，需说明碰撞）。
5. **工程加分**：Redis key 设计、RoaringBitmap、与 Bloom Filter / HyperLogLog 的选型对比。

## 相关文档

- 集合框架选型与 HashSet 对比见 [集合类总览](./jdk/集合类总览.md)。
- 并发场景下的共享 Bitmap 需自行保证线程安全或使用 Redis 原子命令。
