from __future__ import annotations

import io
import os
import uuid
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("DIGICHEF_JSON_PATH", "data/digichef_store.test.json")
os.environ.setdefault("DIGICHEF_UPLOADS_DIR", "data/digichef_uploads_test")

from api import app


class DigiChefApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_public_pages_and_products_api(self) -> None:
        home_response = self.client.get("/digichef")
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("猛見樂後 DigiChef", home_response.text)

        menu_response = self.client.get("/digichef/menu")
        self.assertEqual(menu_response.status_code, 200)
        self.assertIn("套餐總覽", menu_response.text)

        products_response = self.client.get("/digichef/api/public/products")
        self.assertEqual(products_response.status_code, 200)
        products = products_response.json()["data"]
        self.assertEqual(len(products), 4)

        product_detail_response = self.client.get("/digichef/api/public/products/A")
        self.assertEqual(product_detail_response.status_code, 200)
        self.assertEqual(product_detail_response.json()["data"]["name"], "輕纖果醋雞胸")

        product_page_response = self.client.get("/digichef/menu/A")
        self.assertEqual(product_page_response.status_code, 200)
        self.assertIn("烤製設定", product_page_response.text)

    def test_dashboard_and_create_records(self) -> None:
        dashboard_before = self.client.get("/digichef/api/admin/dashboard")
        self.assertEqual(dashboard_before.status_code, 200)
        metrics_before = dashboard_before.json()["data"]["metrics"]

        purchases_before = self.client.get("/digichef/api/admin/purchases").json()["data"]
        purchase_response = self.client.post(
            "/digichef/api/admin/purchases",
            json={
                "purchase_date": "2026-04-14",
                "supplier_name": "測試供應商",
                "item_name": "雞胸",
                "item_spec": "3kg/包",
                "quantity": 1,
                "unit": "包",
                "unit_cost": 360,
                "storage_location": "冷藏 A 區",
                "check_result": "pass",
                "photo_url": "https://example.com/purchase.jpg",
                "recorded_by": "測試員工",
                "notes": f"purchase-{uuid.uuid4()}",
            },
        )
        self.assertEqual(purchase_response.status_code, 200)
        self.assertEqual(len(self.client.get("/digichef/api/admin/purchases").json()["data"]), len(purchases_before) + 1)

        batches_before = self.client.get("/digichef/api/admin/batches").json()["data"]
        batch_response = self.client.post(
            "/digichef/api/admin/batches",
            json={
                "batch_code": f"TEST-{uuid.uuid4().hex[:8]}",
                "product_code": "A",
                "protein_source": "雞胸",
                "raw_weight_g": 150,
                "portion_count": 1,
                "rice_wine_cc": 10,
                "apple_vinegar_cc": 5,
                "flour_g": 0,
                "marinade_started_at": "2026-04-14T09:30:00+08:00",
                "planned_cook_date": "2026-04-14",
                "status": "marinating",
                "handled_by": "測試員工",
                "notes": "batch note",
            },
        )
        self.assertEqual(batch_response.status_code, 200)
        self.assertEqual(len(self.client.get("/digichef/api/admin/batches").json()["data"]), len(batches_before) + 1)

        tests_before = self.client.get("/digichef/api/admin/tests").json()["data"]
        test_response = self.client.post(
            "/digichef/api/admin/tests",
            json={
                "test_code": f"T-{uuid.uuid4().hex[:6]}",
                "test_date": "2026-04-14",
                "product_code": "B",
                "texture_style": "酥炸",
                "oven_mode": "Dry Heat",
                "temperature_c": 215,
                "humidity_pct": 0,
                "fan_speed": 4,
                "target_core_temp_c": 73,
                "actual_core_temp_c": 74,
                "raw_weight_g": 150,
                "cooked_weight_g": 123,
                "appearance_score": 4,
                "taste_score": 4,
                "juiciness_score": 3,
                "photo_url": "https://example.com/test.jpg",
                "notes": "first pass",
                "decision": "approved",
                "recorded_by": "測試員工",
            },
        )
        self.assertEqual(test_response.status_code, 200)
        self.assertEqual(len(self.client.get("/digichef/api/admin/tests").json()["data"]), len(tests_before) + 1)

        issues_before = self.client.get("/digichef/api/admin/issues").json()["data"]
        issue_response = self.client.post(
            "/digichef/api/admin/issues",
            json={
                "reported_at": "2026-04-14T11:00:00+08:00",
                "category": "烤箱",
                "title": "上色不均",
                "description": "右後方顏色偏深",
                "action_taken": "暫停該批並拍照",
                "severity": "medium",
                "blocks_service": False,
                "needs_owner_decision": True,
                "reported_by": "測試員工",
                "status": "new",
            },
        )
        self.assertEqual(issue_response.status_code, 200)
        self.assertEqual(len(self.client.get("/digichef/api/admin/issues").json()["data"]), len(issues_before) + 1)

        photos_before = self.client.get("/digichef/api/admin/photos").json()["data"]
        photo_response = self.client.post(
            "/digichef/api/admin/photos",
            json={
                "captured_on": "2026-04-14",
                "product_code": "C",
                "stage": "cut",
                "file_name": f"C_20260414_cut_{uuid.uuid4().hex[:4]}.jpg",
                "drive_url": "https://example.com/photo.jpg",
                "purpose": "測試紀錄",
                "captured_by": "測試員工",
                "review_status": "pending",
                "notes": "photo note",
            },
        )
        self.assertEqual(photo_response.status_code, 200)
        self.assertEqual(len(self.client.get("/digichef/api/admin/photos").json()["data"]), len(photos_before) + 1)

        dashboard_after = self.client.get("/digichef/api/admin/dashboard")
        self.assertEqual(dashboard_after.status_code, 200)
        metrics_after = dashboard_after.json()["data"]["metrics"]
        self.assertGreaterEqual(metrics_after["test_count"], metrics_before["test_count"])
        self.assertGreaterEqual(metrics_after["open_issue_count"], metrics_before["open_issue_count"])

    def test_task_status_update_and_system_pages(self) -> None:
        dashboard = self.client.get("/digichef/api/admin/dashboard").json()["data"]
        task_id = dashboard["tasks"][0]["id"]
        response = self.client.post(
            f"/digichef/api/admin/tasks/{task_id}/status",
            json={"status": "in_progress", "owner_name": "測試員工", "notes": "已開始"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "in_progress")

        dashboard_page = self.client.get("/digichef/dashboard")
        self.assertEqual(dashboard_page.status_code, 200)
        self.assertIn("遠端營運看板", dashboard_page.text)

        sop_page = self.client.get("/digichef/sop")
        self.assertEqual(sop_page.status_code, 200)
        self.assertIn("SOP 主表", sop_page.text)

        system_page = self.client.get("/digichef/system")
        self.assertEqual(system_page.status_code, 200)
        self.assertIn("系統狀態", system_page.text)

    def test_mobile_style_photo_upload_flow(self) -> None:
        upload_response = self.client.post(
            "/digichef/api/admin/uploads",
            data={"bucket": "photos", "preferred_name": "mobile-shot"},
            files={"file": ("mobile.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")},
        )
        self.assertEqual(upload_response.status_code, 200)
        uploaded_url = upload_response.json()["data"]["url"]
        self.assertTrue(uploaded_url.startswith("/digichef/uploads/photos/"))

        uploaded_file_response = self.client.get(uploaded_url)
        self.assertEqual(uploaded_file_response.status_code, 200)
        self.assertEqual(uploaded_file_response.content, b"fake-image-bytes")

        photo_form_response = self.client.post(
            "/digichef/dashboard/forms/photos",
            data={
                "captured_on": "2026-04-14",
                "product_code": "A",
                "stage": "oven",
                "file_name": "",
                "drive_url": "",
                "purpose": "測試紀錄",
                "captured_by": "手機員工",
                "review_status": "pending",
                "notes": "手機直接上傳",
            },
            files={"photo_file": ("oven-shot.jpg", io.BytesIO(b"phone-upload"), "image/jpeg")},
            follow_redirects=False,
        )
        self.assertEqual(photo_form_response.status_code, 303)

        photos = self.client.get("/digichef/api/admin/photos").json()["data"]
        self.assertTrue(any((item.get("drive_url") or "").startswith("/digichef/uploads/photos/") for item in photos))

    def test_mobile_form_uploads_show_up_in_dashboard(self) -> None:
        test_form_response = self.client.post(
            "/digichef/dashboard/forms/tests",
            data={
                "test_code": f"MOBILE-{uuid.uuid4().hex[:6]}",
                "test_date": "2026-04-14",
                "product_code": "B",
                "texture_style": "酥炸",
                "oven_mode": "Dry Heat",
                "temperature_c": 215,
                "humidity_pct": 0,
                "fan_speed": 4,
                "target_core_temp_c": 73,
                "actual_core_temp_c": 74,
                "raw_weight_g": 150,
                "cooked_weight_g": 123,
                "appearance_score": 4,
                "taste_score": 4,
                "juiciness_score": 3,
                "photo_url": "",
                "notes": "手機測試照",
                "decision": "approved",
                "recorded_by": "手機員工",
            },
            files={"photo_file": ("test-shot.jpg", io.BytesIO(b"test-upload"), "image/jpeg")},
            follow_redirects=False,
        )
        self.assertEqual(test_form_response.status_code, 303)

        issue_form_response = self.client.post(
            "/digichef/dashboard/forms/issues",
            data={
                "reported_at": "2026-04-14T11:15",
                "category": "烤箱",
                "title": f"手機異常-{uuid.uuid4().hex[:4]}",
                "description": "現場拍照回報",
                "action_taken": "先停機觀察",
                "severity": "medium",
                "blocks_service": "false",
                "needs_owner_decision": "true",
                "reported_by": "手機員工",
            },
            files={"attachment_file": ("issue-shot.jpg", io.BytesIO(b"issue-upload"), "image/jpeg")},
            follow_redirects=False,
        )
        self.assertEqual(issue_form_response.status_code, 303)

        tests = self.client.get("/digichef/api/admin/tests").json()["data"]
        self.assertTrue(any((item.get("photo_url") or "").startswith("/digichef/uploads/tests/") for item in tests))

        issues = self.client.get("/digichef/api/admin/issues").json()["data"]
        self.assertTrue(any((item.get("attachment_url") or "").startswith("/digichef/uploads/issues/") for item in issues))

        dashboard_page = self.client.get("/digichef/dashboard")
        self.assertEqual(dashboard_page.status_code, 200)
        self.assertIn("直接拍照上傳", dashboard_page.text)
        self.assertIn("/digichef/uploads/tests/", dashboard_page.text)
        self.assertIn("/digichef/uploads/issues/", dashboard_page.text)
