---
name: mutation-testing
description: 在單元測試通過後觸發。透過引入人工錯誤（Mutants）來「測試你的測試」，確保測試案例具有足夠的錯誤偵測能力，建立對驗證機制的信任（Trust the Verification）。
---

# Mutation Testing Skill

## 觸發時機

- 單元測試覆蓋率達標（如 > 80%）但仍需確認測試品質時
- 核心演算法或高風險模組開發完成後
- CI/CD 流程中的品質閘門（Quality Gate）階段
- 使用者要求「驗證測試有效性」時
- PR Review 時發現測試僅做 smoke test 而缺乏深度驗證

## 核心任務

執行變異測試（Mutation Testing），量化測試套件的品質，找出「倖存的變異體（Surviving Mutants）」，並據此強化測試案例。

---

## 為什麼需要變異測試？

單元測試覆蓋率（Line Coverage）只能告訴你「程式碼被執行到了」，但無法告訴你「測試是否驗證了正確的行為」。

> **"Coverage only checks if the code is executed, Mutation Testing checks if the code is verified."**

### 運作原理

1.  **變異 (Mutate)**：工具自動修改原始碼的一小部分（例如將 `a + b` 改為 `a - b`，或將 `return true` 改為 `return false`），產生一個「變異體 (Mutant)」。
2.  **測試 (Test)**：針對這個變異體執行現有的測試套件。
3.  **判定 (Verdict)**：
    *   **Killed (殺死)**：如果測試失敗（紅燈），表示測試成功偵測到了這個變異，這是**好事**。
    *   **Survived (倖存)**：如果測試仍然通過（綠燈），表示測試**無法偵測**這個錯誤，這是**壞事**。

---

## 工具選擇

### Java — PITest (PIT)

目前 Java 生態系最成熟的變異測試工具。

```xml
<!-- pom.xml configuration -->
<plugin>
    <groupId>org.pitest</groupId>
    <artifactId>pitest-maven</artifactId>
    <version>1.15.0</version>
    <dependencies>
        <dependency>
            <groupId>org.pitest</groupId>
            <artifactId>pitest-junit5-plugin</artifactId>
            <version>1.2.1</version>
        </dependency>
    </dependencies>
    <configuration>
        <targetClasses>
            <param>com.yourdomain.core.*</param>
        </targetClasses>
        <targetTests>
            <param>com.yourdomain.core.*Test</param>
        </targetTests>
        <mutators>
            <mutator>STRONGER</mutator>
        </mutators>
        <outputFormats>
            <outputFormat>HTML</outputFormat>
            <outputFormat>XML</outputFormat>
        </outputFormats>
        <timestampedReports>false</timestampedReports>
    </configuration>
</plugin>
```

執行：
```bash
mvn pitest:mutationCoverage
# 報告位置：target/pit-reports/index.html
```

### TypeScript / JavaScript — Stryker Mutator

```bash
npm install --save-dev @stryker-mutator/core @stryker-mutator/jest-runner @stryker-mutator/typescript-checker
npx stryker init  # 互動式建立 stryker.config.mjs
```

```javascript
// stryker.config.mjs
/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  mutate: [
    'src/domain/**/*.ts',
    'src/application/**/*.ts',
    '!src/**/*.spec.ts',
    '!src/**/*.test.ts',
  ],
  testRunner: 'jest',
  checkers: ['typescript'],
  reporters: ['html', 'clear-text', 'progress'],
  coverageAnalysis: 'perTest',
  thresholds: {
    high: 80,
    low: 60,
    break: 50,   // mutation score 低於此值則 CI 失敗
  },
};
```

執行：
```bash
npx stryker run
# 報告位置：reports/mutation/html/index.html
```

### Go — Gremlins

```bash
go install github.com/go-gremlins/gremlins/cmd/gremlins@latest
```

```bash
# 針對特定 package 執行
gremlins unleash ./internal/domain/...

# 指定測試 timeout（避免無窮迴圈變異體）
gremlins unleash --timeout 30s ./internal/domain/...

# 輸出 JSON 報告
gremlins unleash --output json ./internal/domain/... > mutation-report.json
```

### Rust — cargo-mutants

```bash
cargo install cargo-mutants
```

```bash
# 基本執行
cargo mutants

# 針對特定模組
cargo mutants --file src/domain/aggregate.rs

# 排除測試程式碼
cargo mutants --exclude '*_test.rs' --exclude 'tests/*'

# 並行執行（加速）
cargo mutants --jobs 4
```

### Python — mutmut

```bash
pip install mutmut
```

```bash
# 執行變異測試
mutmut run --paths-to-mutate src/domain/

# 查看倖存者
mutmut results

# 顯示特定變異的 diff
mutmut show 42
```

---

## 變異算子 (Mutators)

常見的變異類型包括：

| 類別 | 原始碼 | 變異後 | 範例 |
|------|--------|--------|------|
| **Conditionals Boundary** | `i < 10` | `i <= 10` | 邊界條件錯誤 |
| **Negate Conditionals** | `a == b` | `a != b` | 邏輯反轉 |
| **Math** | `a + b` | `a - b` | 算術錯誤 |
| **Increments** | `i++` | `i--` | 方向錯誤 |
| **Invert Negatives** | `-i` | `i` | 符號錯誤 |
| **Return Values** | `return true` | `return false` | 回傳值錯誤 |
| **Void Method Calls** | `list.add(x)` | (移除呼叫) | 副作用遺失 |
| **Empty Returns** | `return list` | `return []` | 空集合回傳 |

### 針對 Domain Logic 的高價值變異

以下變異特別適合用於驗證 Domain 層的正確性：

```
Invariant 驗證:
  原始: if (quantity < 0) throw new InvalidQuantityException()
  變異: if (quantity <= 0) throw new InvalidQuantityException()  ← 邊界條件
  變異: (移除整個 if 檢查)                                       ← 遺失守衛

Domain Event 發布:
  原始: domainEvents.add(new OrderCreatedEvent(orderId))
  變異: (移除 add 呼叫)                                         ← 事件遺失

狀態轉換:
  原始: this.status = OrderStatus.CONFIRMED
  變異: this.status = OrderStatus.CANCELLED                      ← 錯誤狀態
```

---

## 分析流程

```
1. 執行單元測試 (必須全數通過)
       ↓
2. 選擇目標範圍 (Domain / Application 層)
       ↓
3. 執行變異測試
       ↓
4. 產生報告
       ↓
5. 分析倖存變異體 (Analyze Surviving Mutants)
       ↓
6. 分類倖存原因 (Missing Assertion / Weak Assertion / Equivalent Mutant)
       ↓
7. 強化測試案例 (Add/Refine Test Cases)
       ↓
8. 重複直到 Mutation Score 達標
```

### 判定標準

| 指標 | 建議閾值 | 說明 |
|------|---------|------|
| **Line Coverage** | > 85% | 基礎要求 |
| **Mutation Score** | > 80% | 殺死的變異體 / 總變異體 |
| **Test Strength** | > 80% | 只計算有被覆蓋到的程式碼的變異分數 |

---

## 常見的倖存原因與對策

### 1. 缺乏斷言 (Missing Assertion)

測試執行了代碼，但沒有檢查結果。

**Java 範例**：
```java
// BAD: 只執行，不驗證
@Test
void createOrder() {
    orderService.createOrder(input);
    // 沒有任何 assert！
}

// GOOD: 驗證狀態與事件
@Test
void createOrder_shouldPublishEvent() {
    var result = orderService.createOrder(input);

    assertThat(result.getStatus()).isEqualTo(OrderStatus.CREATED);
    assertThat(result.getDomainEvents())
        .hasSize(1)
        .first()
        .isInstanceOf(OrderCreatedEvent.class);
}
```

**TypeScript 範例**：
```typescript
// BAD
it('should create order', () => {
  orderService.createOrder(input);
});

// GOOD
it('should create order and publish event', () => {
  const result = orderService.createOrder(input);

  expect(result.status).toBe(OrderStatus.CREATED);
  expect(result.domainEvents).toHaveLength(1);
  expect(result.domainEvents[0]).toBeInstanceOf(OrderCreatedEvent);
});
```

### 2. 斷言過於寬鬆 (Weak Assertion)

只檢查了部分狀態（例如只檢查 List 不為空，沒檢查內容）。

**Go 範例**：
```go
// BAD: 只檢查長度
func TestGetOrders(t *testing.T) {
    orders := repo.FindByCustomer(customerID)
    assert.NotEmpty(t, orders)
}

// GOOD: 檢查具體屬性
func TestGetOrders(t *testing.T) {
    orders := repo.FindByCustomer(customerID)
    assert.Len(t, orders, 2)
    assert.Equal(t, "ORD-001", orders[0].ID)
    assert.Equal(t, OrderStatusActive, orders[0].Status)
}
```

### 3. 邊界條件未涵蓋 (Boundary Not Covered)

變異算子修改邊界（如 `<` → `<=`），但測試只用了中間值。

**Rust 範例**：
```rust
// Domain rule: quantity must be between 1 and 999
impl OrderItem {
    pub fn new(quantity: u32) -> Result<Self, DomainError> {
        if quantity < 1 || quantity > 999 {
            return Err(DomainError::InvalidQuantity);
        }
        Ok(Self { quantity })
    }
}

// BAD: 只測中間值
#[test]
fn test_valid_quantity() {
    assert!(OrderItem::new(10).is_ok());
}

// GOOD: 測邊界值
#[test]
fn test_quantity_boundaries() {
    // 下界
    assert!(OrderItem::new(0).is_err());   // < 1 → 拒絕
    assert!(OrderItem::new(1).is_ok());    // == 1 → 接受

    // 上界
    assert!(OrderItem::new(999).is_ok());  // == 999 → 接受
    assert!(OrderItem::new(1000).is_err()); // > 999 → 拒絕
}
```

### 4. 等價變異 (Equivalent Mutant)

變異後的代碼在邏輯上與原代碼等價，不可能被殺死。

```java
// 原始碼
for (int i = 0; i < list.size(); i++) { ... }

// 等價變異：改成 != 在此場景下行為相同
for (int i = 0; i != list.size(); i++) { ... }
```

*   **對策**：標記為 False Positive 或忽略。大多數工具會回報這些為 `no_coverage` 或 `survived`，需人工判斷。

### 5. Void Method 副作用未驗證 (Side Effect Not Verified)

```typescript
// BAD: repository.save() 被移除也不會被偵測到
it('should update aggregate', () => {
  service.updateOrder(command);
  // 沒有 verify save 被呼叫
});

// GOOD: 驗證副作用
it('should persist updated aggregate', () => {
  service.updateOrder(command);

  expect(mockRepo.save).toHaveBeenCalledWith(
    expect.objectContaining({ id: orderId, status: 'UPDATED' })
  );
});
```

---

## 與 Problem Frames 的整合

### 針對 Frame Type 的變異策略

| Frame Type | 重點變異目標 | 關鍵測試補強 |
|------------|-------------|-------------|
| **CBF** (Command) | Aggregate invariants, Use Case pre/post-conditions, Domain Events | 驗證狀態轉換完整性、事件發布 |
| **IDF** (Query) | Read Model mapping, Caching logic, Filter conditions | 驗證資料轉換正確性、快取失效 |
| **RIF** (Reactor) | Idempotency checks, Retry logic, Event handler conditions | 驗證冪等性、重試策略、DLQ 處理 |

### 範例：CBF Aggregate 變異分析

```yaml
# 待測 Aggregate: Order
mutation_analysis:
  target: src/domain/order/Order.java
  frame_type: CommandedBehaviorFrame

  focus_areas:
    - name: "Invariant enforcement"
      mutators: [CONDITIONALS_BOUNDARY, NEGATE_CONDITIONALS, REMOVE_CONDITIONALS]
      expected_kill_rate: "> 95%"

    - name: "State transitions"
      mutators: [RETURN_VALUES, VOID_METHOD_CALLS]
      expected_kill_rate: "> 90%"

    - name: "Domain event publishing"
      mutators: [VOID_METHOD_CALLS, EMPTY_RETURNS]
      expected_kill_rate: "> 90%"

    - name: "Pre-condition checks"
      mutators: [NEGATE_CONDITIONALS, REMOVE_CONDITIONALS]
      expected_kill_rate: "> 95%"
```

---

## CI/CD 整合

### GitHub Actions 範例

```yaml
# .github/workflows/mutation-test.yml
name: Mutation Testing

on:
  pull_request:
    paths:
      - 'src/domain/**'
      - 'src/application/**'

jobs:
  mutation-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run unit tests first
        run: mvn test

      - name: Run mutation testing
        run: mvn pitest:mutationCoverage

      - name: Check mutation score threshold
        run: |
          # PIT mutations.xml has per-mutation results; calculate score from totals
          KILLED=$(grep -c 'status="KILLED"' target/pit-reports/mutations.xml) || KILLED=0
          TOTAL=$(grep -c '<mutation ' target/pit-reports/mutations.xml) || TOTAL=0
          if [ "$TOTAL" -eq 0 ]; then
            echo "No mutations found"; exit 1
          fi
          SCORE=$(( KILLED * 100 / TOTAL ))
          if [ "$SCORE" -lt 80 ]; then
            echo "Mutation score $SCORE% is below threshold (80%)"
            exit 1
          fi

      - name: Upload mutation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: mutation-report
          path: target/pit-reports/
```

### TypeScript (Stryker) CI

```yaml
jobs:
  mutation-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npx stryker run
        # stryker.config.mjs 中的 thresholds.break 會控制 exit code
```

---

## 交付產物

執行此 Skill 後，應產出：

1.  **Mutation Report Analysis**：分析主要倖存原因，按 Frame Concern 歸類。
2.  **Improved Test Suite**：新增或修改的測試案例，能殺死之前的倖存者。
3.  **Confidence Assessment**：對該模組品質的信心評估。
4.  **Surviving Mutant Summary**：記錄無法殺死的等價變異，附上理由。

### 輸出格式範例

```markdown
## Mutation Testing Report: Order Aggregate

### Summary
| Metric | Value |
|--------|-------|
| Total Mutants | 127 |
| Killed | 108 |
| Survived | 14 |
| Equivalent (ignored) | 5 |
| Mutation Score | 88.5% |

### Surviving Mutants (by priority)

1. **INV-001: Quantity boundary** (Conditionals Boundary)
   - Location: `Order.java:45`
   - Mutation: `quantity < 1` → `quantity <= 1`
   - Impact: High — allows zero quantity orders
   - Fix: Add boundary test for `quantity = 0` and `quantity = 1`

2. **EVT-001: Event not published** (Void Method Call)
   - Location: `Order.java:72`
   - Mutation: removed `addDomainEvent(new OrderConfirmedEvent(...))`
   - Impact: High — silent event loss
   - Fix: Add assertion verifying event list after confirm()
```

---

## 品質閘門 Checklist

- [ ] 單元測試全部通過
- [ ] Mutation Score >= 80%
- [ ] Domain 層 (Entities, Value Objects) Mutation Score >= 90%
- [ ] 所有 Invariant 相關的變異體都被殺死
- [ ] Domain Event 發布的變異體都被殺死
- [ ] 倖存的等價變異體已標記並說明理由
- [ ] 新增的測試遵循 `coding-standards` 規範

> **注意**：變異測試極其耗時。建議只針對核心 Domain Logic (Entities, Value Objects, Domain Services) 執行，避免對整個專案執行。使用 `coverageAnalysis: 'perTest'`（Stryker）或 PITest 的 `targetClasses` 來限縮範圍。
