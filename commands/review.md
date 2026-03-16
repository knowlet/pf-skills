---
name: review
description: 執行完整的代碼審查流程，涵蓋架構合規、編碼標準、契約驗證與規格一致性
---

請針對使用者指定的代碼變更進行全面審查。

1. 使用 `skills/arch-guard/SKILL.md` 檢查 Clean Architecture 層級依賴是否合規。
2. 使用 `skills/coding-standards/SKILL.md` 及對應語言的 `references/` 檢查編碼規範。
3. 使用 `skills/enforce-contract/SKILL.md` 驗證 pre/post-conditions 和 invariants 是否完整。
4. 使用 `skills/code-reviewer/SKILL.md` 進行綜合評分並產出審查報告。
5. 若有對應的 `docs/specs/` 規格目錄，使用 `skills/spec-compliance-validator/SKILL.md` 交叉比對 Spec == Code。
6. 彙整所有發現，依嚴重度排序，提出修正建議。
