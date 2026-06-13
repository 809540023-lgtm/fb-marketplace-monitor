# Investment Plan V3: LINE, Materials, and Public Event Tracking

## Goal

Upgrade the single-stock investment plan from a one-time report into a recurring intelligence service for members who mostly use LINE.

## Member Experience

1. Member opens the investment plan website.
2. Member clicks "LINE 每日推播".
3. Member adds the LINE Official Account.
4. The platform records consent and LINE userId after account binding is implemented.
5. Member receives daily or weekly updates in LINE.

## 2408 Intelligence Scope

Track the stock plan plus the upstream and industry signals that may affect the plan.

### Raw Material and Cost Signals

- DRAM spot and contract price trend.
- DDR4 and DDR5 pricing.
- Silicon wafer supply and pricing.
- Photoresist and specialty gas supply.
- Packaging and testing material cost.
- Power cost and fab utilization commentary.

### Global Peer and Sector Signals

- Micron, Samsung Electronics, SK Hynix, and other memory-sector stock moves.
- Global semiconductor index trend.
- Major DRAM capex, inventory, and pricing commentary.
- TrendForce or other industry research headlines when publicly available.

### Public Event Tracking

Public event tracking can include:

- Official company announcements.
- Taiwan Stock Exchange disclosures.
- Press releases.
- Investor conference materials.
- News reports from reputable financial media.
- Public business association events.
- Public Japan-side customer, supplier, or partner announcements.

Do not track private executive travel. For questions such as "台塑董事長是否前往日本", the system should only report public evidence and label unverified items as unconfirmed.

## LINE Delivery

Use LINE Official Account + Messaging API.

Recommended phases:

1. Add official account link on website.
2. Capture member consent.
3. Bind member account to LINE userId.
4. Generate daily plan summary.
5. Send push messages to subscribed members.
6. Add unsubscribe and delivery log.

## Daily LINE Message Shape

```text
2408 南亞科每日追蹤

今日重點：
- 股價/成交量摘要
- DRAM/原料/全球同業訊號
- 公開事件摘要

本月計畫建議：
暫停投入 / 固定買進 / 小幅加碼 / 分批停利 / 風險檢查

下一步：
追蹤月營收、毛利率、DRAM 報價與最新公告。
```
