from __future__ import annotations

import argparse
import json
from datetime import datetime

from config import settings
from services import PipelineService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CrewAI marketplace content pipeline.")
    parser.add_argument("--query", default=settings.default_query, help="Marketplace 搜尋關鍵字")
    parser.add_argument("--location", default=settings.default_location_name, help="Marketplace 搜尋地區")
    parser.add_argument("--max-results", type=int, default=settings.default_max_results, help="最大抓取筆數")
    parser.add_argument("--publish", action="store_true", help="嘗試執行平台發文流程")
    parser.add_argument("--force", action="store_true", help="忽略日夜排程守門規則，強制執行")
    return parser.parse_args()


def should_run_now() -> tuple[bool, str]:
    now = datetime.now(settings.timezone_info())
    hour = now.hour
    minute = now.minute
    night_hours = {
        int(part.strip())
        for part in settings.night_run_hours.split(",")
        if part.strip().isdigit()
    }

    if settings.daytime_start_hour <= hour < settings.nighttime_start_hour:
        return True, f"daytime_window:{hour:02d}:{minute:02d}"

    if hour in night_hours and minute < 30:
        return True, f"night_window:{hour:02d}:{minute:02d}"

    return False, f"skip_at:{hour:02d}:{minute:02d}"


def main() -> None:
    args = parse_args()
    if not args.force:
        allowed, reason = should_run_now()
        if not allowed:
            print("######################")
            print("## 排程略過本輪執行 ##")
            print("######################")
            print(
                json.dumps(
                    {
                        "status": "skipped",
                        "reason": reason,
                        "timezone": settings.schedule_timezone,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

    result = PipelineService().run(
        query=args.query,
        location=args.location,
        max_results=args.max_results,
        publish=args.publish,
    )

    print("######################")
    print("## 任務執行完成報告 ##")
    print("######################")
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
