---
name: generate-acceptance-test
description: 從規格目錄的 acceptance.yaml 生成/維護 BDD/ezSpec 測試。使用類似 Gherkin 語法，AI 自動產生 step definition（開發人員不需要手寫），驗收測試規格即為 Executable Specification。
---

# Generate Acceptance Test Skill

## 觸發時機

- analyze-frame 產生規格目錄後
- acceptance.yaml 更新時
- 需求異動需同步更新驗收測試時
- 代碼生成前，希望先鎖定可執行的驗收測試

## 核心任務

1. 解析 acceptance.yaml 的測試規格
2. **自動生成 ezSpec step definition（開發人員不需要手寫）**
3. 維護規格與測試的一致性
4. 建立與 Frame Concerns 的可追溯連結

---

## 工具腳本 (scripts/)

### generate_tests.py - 測試生成器

從 acceptance.yaml 生成各語言的 BDD 測試骨架。支援新格式 (`acceptance_criteria`) 和舊格式 (`scenarios`)。

**使用方式：**

```bash
# 生成 Gherkin .feature 檔案
python ~/.claude/skills/generate-acceptance-test/scripts/generate_tests.py \
    docs/specs/create-workflow/ --lang gherkin

# 生成 TypeScript Cucumber.js step definitions
python ~/.claude/skills/generate-acceptance-test/scripts/generate_tests.py \
    docs/specs/create-workflow/ --lang typescript --output tests/acceptance/

# 生成 Go Ginkgo 測試
python ~/.claude/skills/generate-acceptance-test/scripts/generate_tests.py \
    docs/specs/create-workflow/ --lang go --output tests/acceptance/

# 生成 Rust cucumber-rs 測試
python ~/.claude/skills/generate-acceptance-test/scripts/generate_tests.py \
    docs/specs/create-workflow/ --lang rust --output tests/acceptance/
```

**支援語言：**

| Language | Flag | Output |
|----------|------|--------|
| Gherkin | `--lang gherkin` | `{feature}.feature` |
| TypeScript | `--lang typescript` | `{feature}.steps.ts` |
| Go | `--lang go` | `{feature}_test.go` |
| Rust | `--lang rust` | `{feature}.rs` |

**格式相容性：**

腳本自動偵測並支援兩種格式：

```yaml
# 新格式 (推薦)
acceptance_criteria:
  - id: AC1
    trace:
      requirement: [CBF-REQ-1]
      frame_concerns: [FC1]
    given: ["..."]
    when: ["..."]
    then: ["..."]

# 舊格式 (向下相容)
acceptance:
  scenarios:
    - id: AT1
      given:
        - condition: "..."
      when:
        - action: "..."
      then:
        - expectation: "..."
```

---

## 關鍵概念

### Executable Specification

- 驗收測試規格 = 可執行的規格
- 使用類似 Gherkin 的 `given/when/then` 語法
- AI 自動生成 step definition，開發人員不需要手寫
- 規格變更時，測試自動同步

### 目錄結構

```
docs/specs/{feature-name}/
├── frame.yaml
├── acceptance.yaml            # 測試規格 (輸入) - 在根目錄
├── requirements/
│   └── cbf-req-1-{feature}.yaml
├── machine/
│   ├── controller.yaml
│   ├── machine.yaml
│   └── use-case.yaml
├── controlled-domain/
│   └── aggregate.yaml
└── ...
```

---

## acceptance.yaml 格式

```yaml
# docs/specs/{feature-name}/acceptance.yaml
# 注意：放在規格根目錄，不是 acceptance/ 子目錄

acceptance_criteria:

  # ---------------------------------------------------------------------------
  # Happy Path - 成功場景
  # ---------------------------------------------------------------------------
  
  - id: AC1
    type: business          # business | technical | edge-case
    test_tier: usecase      # usecase | integration | e2e
    name: "Create a valid workflow (board existence is not synchronously validated)"
    
    # 追溯連結
    trace:
      requirement:
        - CBF-REQ-1
      frame_concerns:
        - WF-FC-AUTH        # Authorization
        - FC2               # Observability & Auditability
    
    # 連結到生成的測試
    tests_anchor:
      - tests#success
      - tests#event-published
    
    # Given-When-Then 規格
    given:
      - "A boardId <boardId> is provided (existence is NOT synchronously validated in this bounded context)"
      - "A user <userId> is authorized to create workflows for that boardId"
    
    when:
      - "The user requests to create a workflow with boardId <boardId> and name <workflowName>"
    
    then:
      - "The request succeeds"
      - "A Workflow is created and belongs to Board <boardId>"
      - "The Workflow has name <workflowName>"
      - "The Workflow is active (not deleted)"
      - "The Workflow starts in an empty structure state (no stages/lanes configured yet)"
    
    and:
      - "A WorkflowCreated domain event is published for downstream consumers"
    
    # 測試資料範例
    examples:
      - boardId: "board-001"
        userId: "user-123"
        workflowName: "First workflow"

  # ---------------------------------------------------------------------------
  # Error Cases
  # ---------------------------------------------------------------------------
  
  - id: AC2
    type: business
    test_tier: usecase
    name: "Reject workflow creation when not authorized"
    
    trace:
      requirement:
        - CBF-REQ-1
      frame_concerns:
        - WF-FC-AUTH
    
    tests_anchor:
      - tests#unauthorized
    
    given:
      - "A boardId <boardId> is provided"
      - "A user <userId> is NOT authorized to create workflows for that boardId"
    
    when:
      - "The user requests to create a workflow with boardId <boardId>"
    
    then:
      - "The request fails with AuthorizationError"
      - "No Workflow is created"
      - "No domain event is published"
    
    examples:
      - boardId: "board-001"
        userId: "unauthorized-user"
```

---

## 生成的 Gherkin .feature 檔案

```gherkin
# docs/specs/create-workflow/generated/create-workflow.feature
# Auto-generated from acceptance.yaml - DO NOT EDIT DIRECTLY
# Last generated: {ISO-8601}
# Validates: WF-FC-AUTH, FC2

@feature-create-workflow
Feature: Create Workflow
  As a board member
  I want to create a workflow for my board
  So that I can organize my work into stages and lanes

  # ===== Happy Path =====
  
  @smoke @api @AC1
  Scenario Outline: Create a valid workflow successfully
    # Trace: CBF-REQ-1
    # Frame Concerns: WF-FC-AUTH, FC2
    Given A boardId <boardId> is provided (existence is NOT synchronously validated in this bounded context)
    And A user <userId> is authorized to create workflows for that boardId
    When The user requests to create a workflow with boardId <boardId> and name <workflowName>
    Then The request succeeds
    And A Workflow is created and belongs to Board <boardId>
    And The Workflow has name <workflowName>
    And The Workflow is active (not deleted)
    And The Workflow starts in an empty structure state (no stages/lanes configured yet)
    And A WorkflowCreated domain event is published for downstream consumers

    Examples:
      | boardId   | userId   | workflowName   |
      | board-001 | user-123 | First workflow |

  # ===== Error Cases =====
  
  @security @AC2
  Scenario Outline: Reject workflow creation when not authorized
    # Trace: CBF-REQ-1
    # Frame Concerns: WF-FC-AUTH
    Given A boardId <boardId> is provided
    And A user <userId> is NOT authorized to create workflows for that boardId
    When The user requests to create a workflow with boardId <boardId>
    Then The request fails with AuthorizationError
    And No Workflow is created
    And No domain event is published

    Examples:
      | boardId   | userId            |
      | board-001 | unauthorized-user |
```

---

## 同步檢查機制

當規格更新時，Skill 會：

1. **偵測變更**：比對 acceptance.yaml 的變更
2. **標記過時測試**：在 .feature 檔案中標記需更新的場景
3. **生成差異報告**：列出需要同步的項目

```yaml
# 同步狀態報告
sync_report:
  generated_at: "2024-12-25T10:00:00Z"
  
  in_sync:
    - AT1
    - AT2
  
  out_of_sync:
    - id: AT3
      reason: "acceptance.yaml updated, feature file not regenerated"
      diff: "then clause changed"
  
  missing:
    - id: AT4
      reason: "New scenario added to acceptance.yaml"
```

---

## 品質檢查清單

- [ ] 每個 scenario 是否都有可執行的 Given/When/Then？
- [ ] 是否涵蓋 happy-path、error-case、edge-case？
- [ ] 是否與 Frame Concerns 建立 validates_concerns 連結？
- [ ] 是否與 contracts 建立 validates_contracts 連結？
- [ ] 測試名稱、檔名是否對應 feature-name？
- [ ] 併發場景是否有測試 (若 FC 包含 Concurrency)？

---

## BDD 框架支援

本 Skill 支援以下語言與 BDD 框架：

| 語言 | 框架 | 特點 |
|------|------|------|
| Java | ezSpec | Fluent API, 無需 step definition |
| Go | Ginkgo + Gomega | BDD 風格, 表格驅動測試 |
| TypeScript | Cucumber.js / Jest-Cucumber | Gherkin 原生支援 |
| Rust | cucumber-rs | Async 支援, 宏輔助 |

---

## 語言特定生成參考

詳細的各語言測試生成範例請參考：

- [Java ezSpec 生成參考](references/JAVA_EZSPEC.md) — Fluent API, 無需 step definition
- [Go 測試生成參考](references/GOLANG.md) — testify + Ginkgo + Gomega
- [TypeScript 測試生成參考](references/TYPESCRIPT.md) — Vitest + Cucumber.js + Jest-Cucumber
- [Rust 測試生成參考](references/RUST.md) — cucumber-rs

### 框架選擇指南

| 考量 | Java | Go | TypeScript | Rust |
|------|------|-----|------------|------|
| **推薦框架** | ezSpec | Ginkgo | Cucumber.js | cucumber-rs |
| **備選** | Cucumber-JVM | godog | jest-cucumber | - |
| **Step Definition** | 自動 (ezSpec) | 內建 | 手寫 | 宏輔助 |
| **非同步支援** | yes | yes | yes | yes (async/await) |
| **表格測試** | Examples | DescribeTable | Scenario Outline | Examples |
| **IDE 支援** | IntelliJ | GoLand | VS Code | rust-analyzer |

---

## 與其他 Skills 的協作

```
analyze-frame
    |
    └── 生成 acceptance.yaml
            |
            └── generate-acceptance-test (本 Skill)
                    |
                    ├── 生成 .feature (Gherkin)
                    ├── 生成 Java ezSpec (Fluent API)
                    ├── 生成 Go Ginkgo tests
                    ├── 生成 TypeScript Cucumber steps
                    ├── 生成 Rust cucumber-rs tests
                    |
                    ├── 連結 → enforce-contract (驗證 contracts)
                    └── 連結 → cross-context (驗證 ACL)
```
