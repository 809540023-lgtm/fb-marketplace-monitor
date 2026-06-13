# Investment Plans Deployment Checklist

## Ready Features

- Single-stock full analysis plan.
- Monthly recurring investment plan.
- Monthly review and recommendation.
- Material and cost tracking fields.
- Public event keyword tracking fields.
- LINE subscription landing page.
- LINE subscription records.
- LINE push connector for Messaging API.

## Required Environment Variables

```bash
LINE_OFFICIAL_ACCOUNT_URL=https://lin.ee/your-official-account
LINE_CHANNEL_ACCESS_TOKEN=your_line_messaging_api_channel_access_token
```

`LINE_OFFICIAL_ACCOUNT_URL` controls the public "加入 LINE 每日推播" button.

`LINE_CHANNEL_ACCESS_TOKEN` is required before the backend can send push messages.

## LINE Rollout Steps

1. Create or confirm the LINE Official Account.
2. Enable Messaging API in LINE Developers.
3. Add `LINE_OFFICIAL_ACCOUNT_URL` to the deployment environment.
4. Add `LINE_CHANNEL_ACCESS_TOKEN` to the deployment environment.
5. Ask members to add the official account from `/investment-plans/line-subscribe`.
6. Record consent and subscription preference.
7. Bind LINE userId by webhook or LINE Login.
8. Start scheduled daily 2408 push messages.

## Important Tracking Boundary

Public event tracking can use public company announcements, stock exchange disclosures, press releases, investor materials, public association events, and reputable news.

Do not track private executive travel. For executive trips such as "台塑董事長前往日本", report only public evidence and mark unverified items as unconfirmed.

## Verification

Run:

```bash
.venv-test/bin/python -m unittest tests.test_school_platform_api tests.test_digichef_api tests.test_investment_plans_api
```
