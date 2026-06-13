# 猛見樂後 DigiChef 營運文件

這一組文件是給 `猛見樂後（DigiChef）` 智能餐盒專案使用的第一版遠端營運規格，目標是先讓老闆不進門市也能管理員工、測試餐點、追蹤進貨與留存 SOP，再把同一套資料結構延伸成網站與後台系統。

## 已建立的線上文件

- Google Sheet：<https://docs.google.com/spreadsheets/d/1AETAPkwlGyMiO_qzNZA0EjiBMj4aRjY2fNYTiexwYmg/edit?usp=drivesdk>
- Google Doc：<https://docs.google.com/document/d/1CFpcOYxLe0cIuXqubSLCLTdL4xEGYqA0-MaKtXiKJds/edit?usp=drivesdk>

## 文件內容

- [01-remote-ops-playbook.md](./01-remote-ops-playbook.md)
  說明 2026-04-14 起的員工遠端交接方式、首日測試流程與管理節點。
- [02-online-management-model.md](./02-online-management-model.md)
  說明線上試算表如何管理進貨、醃製、測試、成品照片、問題回報與 SOP。
- [03-system-spec.md](./03-system-spec.md)
  把營運流程轉成未來網站與後台可直接開發的資料模型與自動化需求。
- [04-first-version-launch-kit.md](./04-first-version-launch-kit.md)
  整合第一版交付內容，包含員工交接話術、4/14 執行清單、測試紀錄表、SOP、遠端管理與網站規劃。

## 目前建議的落地順序

1. 2026-04-14 先讓員工完全照 Google Sheet 與 Google Doc 執行。
2. 先用 3 到 7 天把測試與日常記錄跑順，確認欄位是否夠用。
3. 再把表單欄位轉成網站後台資料表與權限流程。
4. 等餐點與 SOP 穩定後，再往訂閱制下單、會員管理與財務報表擴充。
