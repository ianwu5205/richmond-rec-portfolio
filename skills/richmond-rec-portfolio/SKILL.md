---
name: richmond-rec-portfolio
description: >-
  Use processed attendance.json from richmond-rec-history-to-json to generate
  a portfolio website. Use when the user wants a Richmond Recreation portfolio
  site from existing processed attendance JSON (not when converting CSVs).
disable-model-invocation: true
dependencies:
  - local: ../richmond-rec-history-to-json
---

# Richmond Rec Portfolio → Web

Generate a portfolio website from processed Richmond Recreation attendance JSON.
This skill reads `attendance.json` produced by `/richmond-rec-history-to-json`.
It does **not** invoke that skill or run the converter.

## 前置檢查

1. 尋找輸入 JSON：
   - 使用者有提供路徑就用它
   - 否則在 workspace 找 `attendance.json` / `resources/attendance.json`
2. 如果找不到，**不要自己去跑轉換**，直接告訴使用者：
   > 找不到 Processed JSON，請先執行 `/richmond-rec-history-to-json`
   > 並參考如何匯出: https://richmondrecportfolio.ianwu.tw/how-to
3. 如果找到了，驗證是否符合 `$SKILL_ROOT/../../schemas/attendance.schema.json`

## 產生網頁

讀取 JSON 的 `programHistory`, `membershipScans`, `activityOutcomes`, `personInformation` 來渲染 portfolio 網站。

> **Scaffold:** 網站產生實作尚未加入。找到並通過 schema 驗證的 JSON 後，告訴使用者目前僅完成前置檢查；產生網頁的腳本／樣板將於後續版本提供。
