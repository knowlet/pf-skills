---
name: spec-compliance-validator
description: 驗證規格檔案的完整性與一致性，確保所有必要的規格元素都已定義且符合標準格式。
---

# Spec Compliance Validator Skill

## 觸發時機

- 新規格檔案創建後
- 規格修改後的驗證
- 進入開發階段前的品質門檻
- 與 `multi-model-reviewer` 協作時

## 核心任務

1. **結構完整性**：驗證規格目錄結構
2. **格式合規性**：YAML 格式與 schema 驗證
3. **追溯性檢查**：Frame Concerns ↔ Acceptance Criteria ↔ Tests
4. **跨規格一致性**：標準引用、命名慣例

---

## 驗證項目

### 1. 目錄結構檢查

```yaml
structure_checks:
  required_files:
    - name: "frame.yaml"
      description: "Problem Frame 定義"
      required: true
      
    - name: "acceptance.yaml"
      description: "驗收標準 (根目錄)"
      required: true
      
    - name: "requirements/*.yaml"
      description: "需求規格"
      required: true
      min_count: 1
      
    - name: "machine/machine.yaml"
      description: "Machine 定義"
      required: true
      
    - name: "machine/use-case.yaml"
      description: "Use Case 規格 (CBF)"
      required_if: "frame_type == 'CBF'"
      
    - name: "machine/query.yaml"
      description: "Query 規格 (IDF)"
      required_if: "frame_type == 'IDF'"
      
    - name: "controlled-domain/aggregate.yaml"
      description: "Aggregate 定義"
      required: true
```

### 2. Frame 定義驗證

```yaml
frame_checks:
  - id: FR1
    name: "Frame Type 有效"
    rule: "frame_type ∈ {CBF, IDF, RIF, WPF, TF}"
    
  - id: FR2
    name: "Frame Concerns 完整"
    rule: "每個 concern 必須有 satisfied_by 連結"
    
  - id: FR3
    name: "Phenomena 定義"
    rule: "input/output phenomena 必須定義"
    
  - id: FR4
    name: "Cross-Context 識別"
    rule: "cross_context_dependencies 如有則必須有對應 ACL"
```

### 3. Acceptance Criteria 驗證

```yaml
acceptance_checks:
  - id: AC1
    name: "格式合規"
    rule: "使用 acceptance_criteria 格式 (非舊版 scenarios)"
    expected_format: |
      acceptance_criteria:
        - id: AC1
          given: "前置條件"
          when: "觸發動作"
          then: "預期結果"
          trace: "requirements/req.yaml#REQ1"
    
  - id: AC2
    name: "追溯性完整"
    rule: "每個 AC 必須有 trace 連結到 requirement"
    
  - id: AC3
    name: "Tests Anchor"
    rule: "應定義 tests_anchor 指向測試檔案"
```

### 4. Domain Event 標準驗證

```yaml
domain_event_checks:
  - id: DE1
    name: "標準引用"
    rule: "domain_events 應包含 includes_standard 和 standard_ref"
    expected: |
      domain_events:
        includes_standard: true
        standard_ref: "../../../../shared/domain-event-standard.yaml"
    
  - id: DE2
    name: "Metadata 屬性"
    rule: "使用標準時不需重複定義 id, occurredOn"
    
  - id: DE3
    name: "屬性排序"
    rule: "主要 ID 應為第一個屬性"
```

### 5. Invariant 驗證

```yaml
invariant_checks:
  - id: INV1
    name: "Enforced 位置"
    rule: "每個 invariant 必須有 enforced_in 位置"
    
  - id: INV2
    name: "測試連結"
    rule: "invariant 應有對應的違反測試"
    
  - id: INV3
    name: "共享標準"
    rule: "共同 invariants 應抽取到 shared/invariants.yaml"
```

---

## 輸出格式

### 驗證報告

```
╔═══════════════════════════════════════════════════════════════════╗
║               SPEC COMPLIANCE VALIDATION REPORT                    ║
╠═══════════════════════════════════════════════════════════════════╣
║ Spec Directory: docs/specs/create-workflow/                        ║
║ Frame Type: CBF (Command-Behavior Frame)                          ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ 📁 STRUCTURE                                                       ║
║ ├── ✅ frame.yaml                              EXISTS              ║
║ ├── ✅ acceptance.yaml                         EXISTS              ║
║ ├── ✅ requirements/cbf-req-1-create-workflow.yaml                 ║
║ ├── ✅ machine/machine.yaml                    EXISTS              ║
║ ├── ✅ machine/use-case.yaml                   EXISTS              ║
║ └── ✅ controlled-domain/aggregate.yaml        EXISTS              ║
║                                                                    ║
║ 📋 FRAME DEFINITION                                                ║
║ ├── ✅ FR1: Frame Type Valid                   PASS               ║
║ ├── ✅ FR2: Frame Concerns Complete            PASS               ║
║ ├── ✅ FR3: Phenomena Defined                  PASS               ║
║ └── ⚠️ FR4: Cross-Context Identified           WARNING             ║
║         └─ AuthorizationContext referenced but no ACL defined     ║
║                                                                    ║
║ 📝 ACCEPTANCE CRITERIA                                             ║
║ ├── ✅ AC1: Format Compliant                   PASS               ║
║ ├── ✅ AC2: Traceability Complete              PASS               ║
║ └── ✅ AC3: Tests Anchor Defined               PASS               ║
║                                                                    ║
║ 🎯 DOMAIN EVENTS                                                   ║
║ ├── ✅ DE1: Standard Reference                 PASS               ║
║ ├── ✅ DE2: No Duplicate Metadata              PASS               ║
║ └── ✅ DE3: Property Ordering                  PASS               ║
║                                                                    ║
║ 🔒 INVARIANTS                                                      ║
║ ├── ✅ INV1: Enforced Location                 PASS               ║
║ ├── ⚠️ INV2: Violation Tests                   WARNING             ║
║ │       └─ 2/5 invariants missing violation tests                 ║
║ └── ✅ INV3: Shared Standards                  PASS               ║
║                                                                    ║
╠═══════════════════════════════════════════════════════════════════╣
║ TOTAL: 14/16 PASS, 2 WARNINGS, 0 ERRORS                           ║
║ STATUS: ⚠️ CONDITIONAL PASS                                        ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 問題詳情

```yaml
validation_issues:
  - id: SCV-001
    check: FR4
    severity: warning
    location: "frame.yaml#cross_context_dependencies"
    message: "AuthorizationContext referenced but no ACL specification found"
    
    current: |
      cross_context_dependencies:
        - context: AuthorizationContext
          dependency_type: query
    
    expected: |
      # Should have corresponding file:
      cross-context/authorization.yaml
    
    suggestion: |
      Run: analyze-frame --add-acl AuthorizationContext
      
  - id: SCV-002
    check: INV2
    severity: warning
    location: "controlled-domain/aggregate.yaml#invariants"
    message: "Invariants missing violation tests"
    
    missing_tests:
      - invariant: "workflow_name_unique_in_board"
        expected_test: "should reject duplicate workflow name"
      - invariant: "max_stages_limit"
        expected_test: "should reject when exceeding max stages"
```

---

## 與其他 Skills 協作

```
┌─────────────────────────────────────────────────────────────────┐
│                     Validation Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────┐                                    │
│  │   spec-compliance-      │ ◄── 本 Skill (第一道防線)           │
│  │   validator             │                                    │
│  │   (規格完整性驗證)        │                                    │
│  └───────────┬─────────────┘                                    │
│              │ Spec 完整                                         │
│              ▼                                                   │
│  ┌─────────────────────────┐                                    │
│  │   code-reviewer         │                                    │
│  │   (程式碼審查)           │                                    │
│  └───────────┬─────────────┘                                    │
│              │ Code 符合規格                                     │
│              ▼                                                   │
│  ┌─────────────────────────┐                                    │
│  │   multi-model-reviewer  │                                    │
│  │   (多模型交叉驗證)        │                                    │
│  └───────────┬─────────────┘                                    │
│              │ 三角驗證通過                                      │
│              ▼                                                   │
│         ✅ Ready for PR                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 標準參考檔案

### 共用標準位置

```yaml
shared_standards:
  domain_events: "shared/domain-event-standard.yaml"
  invariants: "shared/invariants-standard.yaml"
  metadata: "shared/metadata-standard.yaml"
```

### domain-event-standard.yaml 範例

```yaml
# shared/domain-event-standard.yaml
standard:
  name: "Domain Event Standard"
  version: "1.0"
  
base_properties:
  - name: id
    type: EventId
    description: "事件唯一識別碼"
    
  - name: occurredOn
    type: Instant
    description: "事件發生時間"
    
  - name: metadata
    type: EventMetadata
    description: "事件元資料 (correlationId, causationId, userId)"
    
usage:
  includes_standard: true
  standard_ref: "path/to/domain-event-standard.yaml"
  # 使用標準後，只需定義特定屬性，base_properties 自動繼承
```

---

## 配置檔案

### .spec-validator.yaml

```yaml
version: "1.0"

structure:
  strict: true
  required_dirs:
    - requirements
    - machine
    - controlled-domain
    
format:
  acceptance: "acceptance_criteria"  # new format
  allow_legacy: false  # reject old 'scenarios' format
  
traceability:
  require_trace: true
  require_tests_anchor: true
  
standards:
  domain_events:
    require_standard_ref: true
    standard_path: "shared/domain-event-standard.yaml"
    
  invariants:
    require_enforced_in: true
    require_violation_tests: true

ignore:
  paths:
    - "**/_draft/**"
    - "**/_deprecated/**"
```
