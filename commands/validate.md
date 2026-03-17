---
name: validate
description: 驗證規格目錄的完整性與代碼的規格一致性
---

請對使用者指定的功能進行完整驗證。

1. 使用 `skills/spec-compliance-validator/SKILL.md` 驗證 `docs/specs/` 下的規格目錄結構完整性。
2. 使用 `skills/analyze-frame/scripts/validate_spec.py` 自動化驗證 YAML 格式與關聯性。
3. 若有對應的實作代碼，使用 `skills/enforce-contract/SKILL.md` 驗證契約完整性（pre/post-conditions、invariants）。
4. 若有對應的實作代碼，使用 `skills/code-reviewer/SKILL.md` 比對 Spec ↔ Code 一致性（架構合規、規格對照）。
5. 使用 `skills/generate-acceptance-test/SKILL.md` 檢查驗收測試是否涵蓋所有 Frame Concerns。
6. 輸出驗證報告，列出缺失項目與建議修正。
