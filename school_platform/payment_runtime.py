from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import json
from typing import Any

import httpx

from school_platform.config import SchoolPlatformSettings, load_settings


def _minor_units(amount: float, currency: str) -> int:
    currency_code = currency.lower()
    if currency_code in {"jpy", "krw"}:
        return int(round(amount))
    return int(round(amount * 100))


@dataclass(slots=True)
class SchoolPlatformPaymentRuntime:
    settings: SchoolPlatformSettings | None = None

    def __post_init__(self) -> None:
        if self.settings is None:
            self.settings = load_settings()

    def status(self) -> dict[str, Any]:
        provider = self.settings.payment_provider
        stripe_secret_present = bool(self.settings.stripe_secret_key)
        stripe_webhook_present = bool(self.settings.stripe_webhook_secret)
        success_url = self._success_url_template()
        cancel_url = self._cancel_url_template()
        ready = provider == "mock" or (
            provider == "stripe"
            and stripe_secret_present
            and stripe_webhook_present
            and bool(success_url)
            and bool(cancel_url)
        )
        return {
            "provider": provider,
            "ready": ready,
            "currency": self.settings.payment_currency.upper(),
            "stripe_secret_key_present": stripe_secret_present,
            "stripe_publishable_key_present": bool(self.settings.stripe_publishable_key),
            "stripe_webhook_secret_present": stripe_webhook_present,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "app_base_url": self.settings.app_base_url,
            "mode": "external" if provider == "stripe" else "mock",
            "supported_methods": ["card", "transfer", "cash"],
            "message": self._status_message(provider, ready),
        }

    def _status_message(self, provider: str, ready: bool) -> str:
        if provider == "mock":
            return "使用內建 mock 金流。"
        if provider == "stripe" and ready:
            return "Stripe Checkout 已可用。"
        if provider == "stripe":
            return "Stripe 已指定，但尚未補齊 secret key / webhook secret / return URLs。"
        return f"未知金流 provider：{provider}"

    def _success_url_template(self) -> str:
        return (
            self.settings.stripe_success_url
            or f"{self.settings.app_base_url.rstrip('/')}/school-platform/payment"
            "?email={CHECKOUT_EMAIL}&order_no={CHECKOUT_ORDER_NO}&payment_result=success"
        )

    def _cancel_url_template(self) -> str:
        return (
            self.settings.stripe_cancel_url
            or f"{self.settings.app_base_url.rstrip('/')}/school-platform/payment"
            "?email={CHECKOUT_EMAIL}&order_no={CHECKOUT_ORDER_NO}&payment_result=cancel"
        )

    def _require_stripe_ready(self) -> None:
        status = self.status()
        if status["provider"] != "stripe":
            raise RuntimeError("Payment provider is not set to stripe.")
        if not status["ready"]:
            raise RuntimeError(status["message"])

    def create_checkout_session(
        self,
        *,
        order_no: str,
        amount: float,
        payment_method: str,
        student_email: str,
        product_name: str,
        enrollment_id: str,
    ) -> dict[str, Any]:
        provider = self.settings.payment_provider
        if provider == "mock" or payment_method != "card":
            return {
                "provider": "mock",
                "provider_payment_id": None,
                "checkout_url": None,
                "client_token": f"demo_{order_no}",
                "provider_status": "pending",
                "currency": self.settings.payment_currency.upper(),
            }

        self._require_stripe_ready()
        success_url = self._success_url_template().replace("{CHECKOUT_EMAIL}", student_email).replace("{CHECKOUT_ORDER_NO}", order_no)
        cancel_url = self._cancel_url_template().replace("{CHECKOUT_EMAIL}", student_email).replace("{CHECKOUT_ORDER_NO}", order_no)
        payload = [
            ("mode", "payment"),
            ("success_url", success_url),
            ("cancel_url", cancel_url),
            ("customer_email", student_email),
            ("client_reference_id", order_no),
            ("metadata[order_no]", order_no),
            ("metadata[student_email]", student_email),
            ("metadata[enrollment_id]", enrollment_id),
            ("line_items[0][price_data][currency]", self.settings.payment_currency),
            ("line_items[0][price_data][unit_amount]", str(_minor_units(amount, self.settings.payment_currency))),
            ("line_items[0][price_data][product_data][name]", product_name[:120]),
            ("line_items[0][quantity]", "1"),
            ("payment_method_types[0]", "card"),
        ]
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                data=payload,
                auth=(self.settings.stripe_secret_key or "", ""),
            )
        response.raise_for_status()
        data = response.json()
        return {
            "provider": "stripe",
            "provider_payment_id": data.get("id"),
            "checkout_url": data.get("url"),
            "client_token": data.get("id") or "",
            "provider_status": data.get("status") or "open",
            "currency": str(data.get("currency") or self.settings.payment_currency).upper(),
            "raw": data,
        }

    def verify_and_parse_stripe_event(self, payload: bytes, signature_header: str | None) -> dict[str, Any]:
        self._require_stripe_ready()
        if not signature_header:
            raise RuntimeError("Stripe-Signature header is missing.")
        timestamp = None
        signatures: list[str] = []
        for part in signature_header.split(","):
            key, _, value = part.partition("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                signatures.append(value)
        if not timestamp or not signatures:
            raise RuntimeError("Stripe-Signature header is invalid.")
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
        expected = hmac.new(
            (self.settings.stripe_webhook_secret or "").encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if not any(hmac.compare_digest(expected, signature) for signature in signatures):
            raise RuntimeError("Stripe webhook signature verification failed.")
        return json.loads(payload.decode("utf-8"))

    def normalize_webhook_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        event_type = str(event.get("type") or "")
        data = event.get("data", {})
        obj = data.get("object", {}) if isinstance(data, dict) else {}
        metadata = obj.get("metadata", {}) if isinstance(obj, dict) else {}
        order_no = metadata.get("order_no") or obj.get("client_reference_id")
        if not order_no:
            return None
        if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded", "payment_intent.succeeded"}:
            status = "paid"
        elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed", "payment_intent.payment_failed"}:
            status = "failed"
        elif event_type in {"charge.refunded", "charge.refund.updated"}:
            status = "refunded"
        else:
            return None
        paid_at = datetime.now().astimezone().isoformat() if status == "paid" else None
        return {
            "order_no": order_no,
            "status": status,
            "provider": "stripe",
            "provider_payment_id": obj.get("payment_intent") or obj.get("id"),
            "provider_status": obj.get("payment_status") or obj.get("status") or event_type,
            "event_type": event_type,
            "paid_at": paid_at,
        }
