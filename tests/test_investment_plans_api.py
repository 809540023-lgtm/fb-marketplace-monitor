from __future__ import annotations

import tempfile
import unittest
import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from api import app
from connectors.notifications import LineNotifier
from investment_plans.service import InvestmentPlanStore


class InvestmentPlansApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.investment_router = importlib.import_module("investment_plans.router")
        self.investment_router.store = InvestmentPlanStore(Path(self.tempdir.name) / "plans.json")
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_create_recurring_investment_plan(self) -> None:
        response = self.client.post(
            "/investment-plans/api/plans",
            json={
                "user_id": "member-001",
                "stock_symbol": "2408",
                "stock_name": "南亞科",
                "plan_type": "recurring_investment",
                "current_price": 324,
                "monthly_amount": 3000,
                "investment_years": 5,
                "risk_profile": "balanced",
                "industry_cycle": "cyclical",
                "valuation_level": "expensive",
                "max_loss_percent": 25,
                "target_return_percent": 50,
            },
        )
        self.assertEqual(response.status_code, 200)
        plan = response.json()["data"]
        self.assertEqual(plan["request"]["plan_type"], "recurring_investment")
        self.assertEqual(plan["allocation"]["monthly_amount"], 3000)
        self.assertGreater(plan["allocation"]["cash_reserve_ratio"], 0.3)
        self.assertIn("每月零存整付", plan["title"])
        self.assertGreaterEqual(len(plan["price_bands"]), 4)
        self.assertGreaterEqual(len(plan["action_rules"]), 4)

        list_response = self.client.get("/investment-plans/api/plans?user_id=member-001")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["data"]), 1)

    def test_create_full_analysis_plan(self) -> None:
        response = self.client.post(
            "/investment-plans/api/plans",
            json={
                "user_id": "member-002",
                "stock_symbol": "2330",
                "stock_name": "台積電",
                "plan_type": "full_analysis",
                "current_price": 1000,
                "investment_years": 10,
                "risk_profile": "balanced",
                "industry_cycle": "growth",
                "valuation_level": "fair",
            },
        )
        self.assertEqual(response.status_code, 200)
        plan = response.json()["data"]
        self.assertEqual(plan["request"]["plan_type"], "full_analysis")
        self.assertIn("完整股票分析", plan["title"])
        self.assertIsNone(plan["allocation"]["monthly_amount"])
        self.assertEqual(plan["allocation"]["total_planned_contribution"], 0)

    def test_create_monthly_review_for_existing_plan(self) -> None:
        plan_response = self.client.post(
            "/investment-plans/api/plans",
            json={
                "user_id": "member-review",
                "stock_symbol": "2408",
                "stock_name": "南亞科",
                "plan_type": "recurring_investment",
                "current_price": 324,
                "monthly_amount": 3000,
                "investment_years": 5,
                "risk_profile": "balanced",
                "industry_cycle": "cyclical",
                "valuation_level": "expensive",
            },
        )
        self.assertEqual(plan_response.status_code, 200)
        plan_id = plan_response.json()["data"]["id"]

        review_response = self.client.post(
            f"/investment-plans/api/plans/{plan_id}/reviews",
            json={
                "current_price": 275,
                "average_cost": 324,
                "shares_owned": 10,
                "available_cash": 3000,
                "revenue_trend": "stable",
                "earnings_trend": "stable",
                "valuation_level": "fair",
            },
        )
        self.assertEqual(review_response.status_code, 200)
        review = review_response.json()["data"]
        self.assertEqual(review["plan_id"], plan_id)
        self.assertIn(review["recommendation"], {"buy", "add", "hold", "pause", "take_profit", "risk_review"})
        self.assertGreaterEqual(review["suggested_cash_reserve"], 0)
        self.assertTrue(review["price_position"])

        reviews_response = self.client.get(f"/investment-plans/api/plans/{plan_id}/reviews")
        self.assertEqual(reviews_response.status_code, 200)
        self.assertEqual(len(reviews_response.json()["data"]), 1)

        detail_response = self.client.get(f"/investment-plans/{plan_id}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("Latest Monthly Review", detail_response.text)

        review_page_response = self.client.get(f"/investment-plans/{plan_id}/review")
        self.assertEqual(review_page_response.status_code, 200)
        self.assertIn("本月更新", review_page_response.text)

    def test_recurring_plan_requires_monthly_amount(self) -> None:
        response = self.client.post(
            "/investment-plans/api/plans",
            json={
                "user_id": "member-003",
                "stock_symbol": "2408",
                "plan_type": "recurring_investment",
                "current_price": 324,
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_html_pages_render(self) -> None:
        home = self.client.get("/investment-plans")
        self.assertEqual(home.status_code, 200)
        self.assertIn("完整分析 + 每月零存整付", home.text)

        new_page = self.client.get("/investment-plans/new")
        self.assertEqual(new_page.status_code, 200)
        self.assertIn("建立會員單股投資計畫", new_page.text)
        self.assertIn("原料/成本追蹤", new_page.text)

        line_page = self.client.get("/investment-plans/line-subscribe")
        self.assertEqual(line_page.status_code, 200)
        self.assertIn("每天用 LINE 收 2408 投資更新", line_page.text)
        self.assertIn("建立推播訂閱", line_page.text)

    def test_line_subscription_api_and_safe_notifier_fallback(self) -> None:
        response = self.client.post(
            "/investment-plans/api/line-subscriptions",
            json={
                "user_id": "member-line",
                "frequency": "daily",
                "consent": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        subscription = response.json()["data"]
        self.assertEqual(subscription["user_id"], "member-line")
        self.assertEqual(subscription["status"], "pending_binding")

        list_response = self.client.get("/investment-plans/api/line-subscriptions?user_id=member-line")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["data"]), 1)

        text = LineNotifier().build_investment_text(
            title="2408 南亞科每日追蹤",
            summary="股價與 DRAM 報價維持觀察。",
            recommendation="本月暫停追價",
            plan_url="https://example.com/plan",
        )
        self.assertIn("2408 南亞科每日追蹤", text)
        self.assertIn("本月暫停追價", text)
        self.assertIn("略過 LINE 推播", LineNotifier().send_push("", text))
