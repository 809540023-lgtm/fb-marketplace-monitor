from __future__ import annotations

import argparse
import json
import os

import httpx


def _check(name: str, ok: bool, detail: str) -> dict[str, object]:
    return {"name": name, "ok": ok, "detail": detail}


def run_deployment_smoke(base_url: str, email: str, password: str) -> dict[str, object]:
    normalized_base_url = base_url.rstrip("/")
    checks: list[dict[str, object]] = []
    with httpx.Client(base_url=normalized_base_url, timeout=20.0, follow_redirects=True) as client:
        progress = client.get("/school-platform/api/progress")
        progress_payload = progress.json()["data"] if progress.status_code == 200 else {}
        checks.append(
            _check(
                "progress_api",
                progress.status_code == 200 and int(progress_payload.get("tests_passing", 0)) >= 66,
                f"status={progress.status_code}, tests_passing={progress_payload.get('tests_passing', 'n/a')}",
            )
        )

        storage = client.get("/school-platform/api/system/storage")
        storage_payload = storage.json()["data"] if storage.status_code == 200 else {}
        checks.append(
            _check(
                "system_storage",
                storage.status_code == 200
                and bool(storage_payload.get("readiness", {}).get("ready"))
                and "payment_provider" in storage_payload
                and "notification_providers" in storage_payload,
                f"status={storage.status_code}, backend={storage_payload.get('backend', 'n/a')}",
            )
        )

        courses = client.get("/school-platform/api/public/courses")
        course_count = len(courses.json()["data"]) if courses.status_code == 200 else 0
        checks.append(_check("public_courses", courses.status_code == 200 and course_count >= 1, f"status={courses.status_code}, courses={course_count}"))

        classes = client.get("/school-platform/api/public/classes/open")
        class_count = len(classes.json()["data"]) if classes.status_code == 200 else 0
        checks.append(_check("open_classes", classes.status_code == 200 and class_count >= 1, f"status={classes.status_code}, classes={class_count}"))

        login = client.post(
            "/school-platform/api/auth/login",
            json={"email": email, "password": password},
        )
        token = login.json()["data"]["access_token"] if login.status_code == 200 else None
        checks.append(_check("auth_login", login.status_code == 200 and bool(token), f"status={login.status_code}"))

        if token:
            headers = {"Authorization": f"Bearer {token}"}
            reports = client.get("/school-platform/api/reports/overview", headers=headers)
            checks.append(_check("reports_overview", reports.status_code == 200, f"status={reports.status_code}"))

            weekly = client.get("/school-platform/api/reports/weekly-summary", headers=headers)
            checks.append(_check("weekly_summary", weekly.status_code == 200, f"status={weekly.status_code}"))

            ai_status = client.get("/school-platform/api/ai/status", headers=headers)
            checks.append(_check("ai_status", ai_status.status_code == 200, f"status={ai_status.status_code}"))

            recruiting_jobs = client.get("/school-platform/api/recruiting/jobs", headers=headers)
            checks.append(_check("recruiting_jobs", recruiting_jobs.status_code == 200, f"status={recruiting_jobs.status_code}"))

            finance = client.get("/school-platform/api/finance/overview", headers=headers)
            checks.append(_check("finance_overview", finance.status_code == 200, f"status={finance.status_code}"))

            messages = client.get("/school-platform/api/messages/overview", headers=headers)
            message_payload = messages.json()["data"] if messages.status_code == 200 else {}
            checks.append(
                _check(
                    "messages_overview",
                    messages.status_code == 200 and "providers" in message_payload,
                    f"status={messages.status_code}",
                )
            )

    return {
        "base_url": normalized_base_url,
        "auth_email": email,
        "checks": checks,
        "success": all(bool(item["ok"]) for item in checks),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("SCHOOL_PLATFORM_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--email", default=os.getenv("SCHOOL_PLATFORM_SMOKE_EMAIL", "manager@jls.local"))
    parser.add_argument("--password", default=os.getenv("SCHOOL_PLATFORM_SMOKE_PASSWORD", "manager123"))
    args = parser.parse_args()

    report = run_deployment_smoke(args.base_url, args.email, args.password)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
