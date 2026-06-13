from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from html import unescape
from typing import ClassVar
from urllib.request import urlopen

from crewai.tools import BaseTool
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel, Field

from config import settings


class InventoryFolderScanInput(BaseModel):
    folder_name: str | None = Field(default=None, description="指定日期資料夾名稱，例如 20260101。留空則抓最新日期資料夾。")


class GoogleDriveInventoryTool(BaseTool):
    name: str = "google_drive_inventory_scanner"
    description: str = "掃描 Google Drive 的 agai2_new 進貨圖片資料夾，依日期資料夾與檔名分組圖片。"
    args_schema: type[BaseModel] = InventoryFolderScanInput
    IMAGE_MIME_PREFIX: ClassVar[str] = "image/"

    def _credentials(self) -> Credentials:
        if not settings.google_service_account_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON 尚未設定。")
        service_account_info = json.loads(settings.google_service_account_json)
        return Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

    def _drive(self):
        return build("drive", "v3", credentials=self._credentials(), cache_discovery=False)

    def _embedded_folder_html(self, folder_id: str) -> str:
        url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#grid"
        with urlopen(url) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _parse_embedded_entries(self, html: str) -> list[dict[str, str]]:
        pattern = re.compile(
            r'<div class="flip-entry" id="entry-([^"]+)".*?<a href="([^"]+)"[^>]*>.*?<div class="flip-entry-title">(.*?)</div>',
            re.S,
        )
        entries: list[dict[str, str]] = []
        for entry_id, href, title in pattern.findall(html):
            entry_type = "folder" if "/drive/folders/" in href else "file"
            entries.append(
                {
                    "id": entry_id.strip(),
                    "href": href.strip(),
                    "title": unescape(re.sub(r"<[^>]+>", "", title)).strip(),
                    "type": entry_type,
                }
            )
        return entries

    def _public_folder_entries(self, folder_id: str) -> list[dict[str, str]]:
        return self._parse_embedded_entries(self._embedded_folder_html(folder_id))

    def _root_folder_id(self, drive) -> str:
        if settings.google_drive_root_folder_id:
            return settings.google_drive_root_folder_id

        query = (
            "mimeType = 'application/vnd.google-apps.folder' "
            f"and name = '{settings.google_drive_root_folder_name}' and trashed = false"
        )
        response = drive.files().list(q=query, fields="files(id,name)", pageSize=5).execute()
        files = response.get("files", [])
        if not files:
            raise ValueError(f"找不到 Google Drive 根資料夾：{settings.google_drive_root_folder_name}")
        return str(files[0]["id"])

    def _date_folders(self, drive, root_folder_id: str) -> list[dict[str, str]]:
        query = (
            f"'{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        response = drive.files().list(
            q=query,
            fields="files(id,name,createdTime)",
            orderBy="name desc",
            pageSize=100,
        ).execute()
        return response.get("files", [])

    def _child_files(self, drive, folder_id: str) -> list[dict[str, str]]:
        query = f"'{folder_id}' in parents and trashed = false"
        response = drive.files().list(
            q=query,
            fields="files(id,name,mimeType,createdTime,webViewLink,thumbnailLink)",
            orderBy="createdTime asc",
            pageSize=500,
        ).execute()
        return response.get("files", [])

    def _image_files(self, drive, folder_id: str) -> list[dict[str, str]]:
        query = f"'{folder_id}' in parents and trashed = false"
        response = drive.files().list(
            q=query,
            fields="files(id,name,mimeType,createdTime,webViewLink,thumbnailLink)",
            orderBy="createdTime asc",
            pageSize=500,
        ).execute()
        files = response.get("files", [])
        return [file for file in files if str(file.get("mimeType", "")).startswith(self.IMAGE_MIME_PREFIX)]

    def _group_key(self, file_name: str) -> str:
        stem = file_name.rsplit(".", 1)[0]
        normalized = re.sub(r"[_\-\s]?[1-4]$", "", stem).strip()
        return normalized or stem

    def _warehouse_date_from_timestamp(self, timestamp: str | None) -> str:
        if not timestamp:
            return datetime.utcnow().strftime("%Y%m%d")
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y%m%d")
        except ValueError:
            return datetime.utcnow().strftime("%Y%m%d")

    def _is_date_folder_name(self, name: str) -> bool:
        return bool(re.fullmatch(r"\d{8}", name))

    def _public_image_url(self, file_id: str) -> str:
        return f"https://drive.google.com/uc?id={file_id}"

    def _run(self, folder_name: str | None = None) -> str:
        if not settings.google_service_account_json and settings.google_drive_root_folder_id:
            return self._run_public(folder_name=folder_name)

        drive = self._drive()
        root_folder_id = self._root_folder_id(drive)
        folders = self._date_folders(drive, root_folder_id)
        if not folders:
            raise ValueError("agai2_new 底下沒有任何子資料夾。")

        date_mode = any(self._is_date_folder_name(str(folder.get("name") or "")) for folder in folders)
        groups: list[dict[str, object]] = []

        if date_mode:
            target_folder = None
            if folder_name:
                target_folder = next((folder for folder in folders if folder.get("name") == folder_name), None)
                if not target_folder:
                    raise ValueError(f"找不到指定日期資料夾：{folder_name}")
            else:
                target_folder = folders[0]

            image_files = self._image_files(drive, str(target_folder["id"]))
            grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
            for file in image_files:
                group_key = self._group_key(str(file.get("name", "")))
                grouped[group_key].append(
                    {
                        "image_name": file.get("name"),
                        "image_url": self._public_image_url(str(file.get("id"))),
                        "image_order": len(grouped[group_key]) + 1,
                        "created_at": file.get("createdTime"),
                    }
                )

            groups = [
                {
                    "source_file_stem": key,
                    "warehouse_date": target_folder.get("name"),
                    "folder_name": target_folder.get("name"),
                    "images": images,
                    "image_count": len(images),
                }
                for key, images in grouped.items()
            ]
            payload = {
                "root_folder_name": settings.google_drive_root_folder_name,
                "folder_name": target_folder.get("name"),
                "folder_id": target_folder.get("id"),
                "structure_mode": "date_folders",
                "groups": groups,
            }
            return json.dumps(payload, ensure_ascii=False)

        target_folders = folders
        if folder_name:
            target_folders = [folder for folder in folders if folder.get("name") == folder_name]
            if not target_folders:
                raise ValueError(f"找不到指定商品資料夾：{folder_name}")

        for product_folder in target_folders:
            product_images = self._image_files(drive, str(product_folder["id"]))
            if not product_images:
                continue
            groups.append(
                {
                    "source_file_stem": str(product_folder.get("name") or ""),
                    "warehouse_date": self._warehouse_date_from_timestamp(str(product_folder.get("createdTime") or "")),
                    "folder_name": str(product_folder.get("name") or ""),
                    "images": [
                        {
                            "image_name": image.get("name"),
                            "image_url": self._public_image_url(str(image.get("id"))),
                            "image_order": index,
                            "created_at": image.get("createdTime"),
                        }
                        for index, image in enumerate(product_images, start=1)
                    ],
                    "image_count": len(product_images),
                }
            )

        payload = {
            "root_folder_name": settings.google_drive_root_folder_name,
            "folder_name": folder_name or settings.google_drive_root_folder_name,
            "folder_id": root_folder_id,
            "structure_mode": "product_folders",
            "groups": groups,
        }
        return json.dumps(payload, ensure_ascii=False)

    def _run_public(self, folder_name: str | None = None) -> str:
        if not settings.google_drive_root_folder_id:
            raise ValueError("GOOGLE_DRIVE_ROOT_FOLDER_ID 尚未設定，且目前沒有 service account 可用。")

        root_folder_id = settings.google_drive_root_folder_id
        folders = [entry for entry in self._public_folder_entries(root_folder_id) if entry.get("type") == "folder"]
        if not folders:
            raise ValueError("公開資料夾底下沒有可用的商品子資料夾。")

        target_folders = folders
        if folder_name:
            target_folders = [folder for folder in folders if folder.get("title") == folder_name]
            if not target_folders:
                raise ValueError(f"找不到指定商品資料夾：{folder_name}")

        groups: list[dict[str, object]] = []
        for product_folder in target_folders:
            entries = self._public_folder_entries(str(product_folder.get("id") or ""))
            image_entries = [entry for entry in entries if entry.get("type") == "file"]
            if not image_entries:
                continue
            groups.append(
                {
                    "source_file_stem": str(product_folder.get("title") or ""),
                    "warehouse_date": datetime.utcnow().strftime("%Y%m%d"),
                    "folder_name": str(product_folder.get("title") or ""),
                    "images": [
                        {
                            "image_name": entry.get("title"),
                            "image_url": self._public_image_url(str(entry.get("id") or "")),
                            "image_order": index,
                            "created_at": None,
                        }
                        for index, entry in enumerate(image_entries, start=1)
                    ],
                    "image_count": len(image_entries),
                }
            )

        payload = {
            "root_folder_name": settings.google_drive_root_folder_name,
            "folder_name": folder_name or settings.google_drive_root_folder_name,
            "folder_id": root_folder_id,
            "structure_mode": "public_shared_folders",
            "groups": groups,
        }
        return json.dumps(payload, ensure_ascii=False)
