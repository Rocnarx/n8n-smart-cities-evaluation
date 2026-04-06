from __future__ import annotations

import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

APP_NAME = "caseA-mock-services"
VERSION = "1.1.0"


def _int_env(name: str, default: int, *, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default



def _float_env(name: str, default: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return max(minimum, min(maximum, float(raw)))
    except ValueError:
        return default


# Global defaults.
# If the request does not send delay_ms/jitter_ms, these values are used automatically.
MIN_DELAY_MS = _int_env("MIN_DELAY_MS", 150)
MAX_DELAY_MS = _int_env("MAX_DELAY_MS", 900)
DEFAULT_JITTER_MS = _int_env("DEFAULT_JITTER_MS", 250)
DEFAULT_FAIL_RATE = _float_env("FAIL_RATE", 0.0)

# Avoid broken ranges coming from environment variables.
if MAX_DELAY_MS < MIN_DELAY_MS:
    MIN_DELAY_MS, MAX_DELAY_MS = MAX_DELAY_MS, MIN_DELAY_MS

RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED not in (None, ""):
    try:
        random.seed(int(RANDOM_SEED))
    except ValueError:
        random.seed(RANDOM_SEED)



def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def sleep_ms(ms: int) -> None:
    if ms > 0:
        time.sleep(ms / 1000.0)



def compute_delay_ms(delay_ms: Optional[int], jitter_ms: Optional[int]) -> int:
    # If delay_ms is explicitly sent, use it as the base.
    # Otherwise pick a random base from the configured global range.
    base = delay_ms if delay_ms is not None else random.randint(MIN_DELAY_MS, MAX_DELAY_MS)

    # If jitter_ms is explicitly sent, use it.
    # Otherwise add a default random jitter to simulate more natural latency variation.
    jitter_cap = DEFAULT_JITTER_MS if jitter_ms is None else jitter_ms
    jitter = random.randint(0, max(0, jitter_cap)) if jitter_cap > 0 else 0
    return max(0, base + jitter)



def should_fail(force_error: Optional[bool], fail_rate: Optional[float]) -> bool:
    if force_error:
        return True
    rate = DEFAULT_FAIL_RATE if fail_rate is None else max(0.0, min(1.0, fail_rate))
    return random.random() < rate


class BaseRequest(BaseModel):
    # Echo fields so the workflow can keep context without merges
    transaction_id: str = Field(..., description="Correlation/transaction id used by the workflow")
    amount: float = Field(0, ge=0, description="Payment amount")
    account_balance: float = Field(0, ge=0, description="Available balance (simulated)")
    # Control knobs
    delay_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Fixed base delay in ms for this call. If omitted, the API uses a random base delay.",
    )
    jitter_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Random jitter (0..jitter_ms) added on top. If omitted, DEFAULT_JITTER_MS is used.",
    )
    fail_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of technical failure (0..1)")
    force_error: Optional[bool] = Field(False, description="If true, force a technical failure (5xx)")


class FundsValidateRequest(BaseRequest):
    force_insufficient: Optional[bool] = Field(False, description="If true, force insufficient funds (business reject)")


class BankConfirmRequest(BaseRequest):
    force_reject: Optional[bool] = Field(False, description="If true, bank will reject (business reject)")


class RecaudoRequest(BaseRequest):
    force_reject: Optional[bool] = Field(False, description="If true, recaudo will reject (business reject)")


class TullaveRequest(BaseRequest):
    force_reject: Optional[bool] = Field(False, description="If true, tullave activation will fail (business reject)")


class DianReportRequest(BaseRequest):
    force_reject: Optional[bool] = Field(False, description="If true, DIAN will reject (business reject)")


class NotifyRequest(BaseRequest):
    channel: str = Field("EMAIL", description="Notification channel")
    force_reject: Optional[bool] = Field(False, description="If true, notification will fail (business reject)")



def build_echo(payload: BaseRequest, service: str) -> Dict[str, Any]:
    return {
        "service": service,
        "transaction_id": payload.transaction_id,
        "amount": payload.amount,
        "account_balance": payload.account_balance,
    }



def build_meta(payload: BaseRequest, simulated_delay_ms: int, x_correlation_id: Optional[str], started_at: float) -> Dict[str, Any]:
    return {
        "correlation_id": x_correlation_id,
        "simulated_delay_ms": simulated_delay_ms,
        "service_latency_ms": int((time.perf_counter() - started_at) * 1000),
        "latency_config": {
            "request_delay_ms": payload.delay_ms,
            "request_jitter_ms": payload.jitter_ms,
            "global_min_delay_ms": MIN_DELAY_MS,
            "global_max_delay_ms": MAX_DELAY_MS,
            "default_jitter_ms": DEFAULT_JITTER_MS,
        },
    }


app = FastAPI(title=APP_NAME, version=VERSION)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": VERSION,
        "time": now_iso(),
        "defaults": {
            "min_delay_ms": MIN_DELAY_MS,
            "max_delay_ms": MAX_DELAY_MS,
            "default_jitter_ms": DEFAULT_JITTER_MS,
            "fail_rate": DEFAULT_FAIL_RATE,
        },
    }


@app.post("/funds/validate")
def funds_validate(req: FundsValidateRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FUNDS_SERVICE_UNAVAILABLE",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )
    funds_ok = (req.account_balance >= req.amount) and (not bool(req.force_insufficient))
    out = build_echo(req, "funds")
    out.update(
        {
            "funds_ok": funds_ok,
            "funds_validation_source": "BANK_CORE",
            "funds_validation_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/bank/confirm")
def bank_confirm(req: BankConfirmRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=502,
            detail={
                "error": "BANK_UPSTREAM_ERROR",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )
    status = "REJECTED" if req.force_reject else "CONFIRMED"
    out = build_echo(req, "bank_confirmation")
    out.update(
        {
            "bank_confirmation_status": status,
            "bank_confirmation_ref": f"BC-{req.transaction_id}",
            "bank_confirmation_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/recaudo/bogota")
def recaudo_bogota(req: RecaudoRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "RECAUDO_TIMEOUT",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )
    status = "REJECTED" if req.force_reject else "OK"
    out = build_echo(req, "recaudo_bogota")
    out.update(
        {
            "recaudo_status": status,
            "recaudo_reference": f"RC-{req.transaction_id}",
            "recaudo_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/tullave/activate")
def tullave_activate(req: TullaveRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "TULLAVE_UNAVAILABLE",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )
    activated = not bool(req.force_reject)
    out = build_echo(req, "tullave")
    out.update(
        {
            "tullave_activated": activated,
            "tullave_activation_time": now_iso(),
            "tullave_message": "Saldo/recarga aplicada (simulado)" if activated else "Activación fallida (simulado)",
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/dian/report")
def dian_report(req: DianReportRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DIAN_GATEWAY_TIMEOUT",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )
    status = "REJECTED" if req.force_reject else "RECEIVED"
    out = build_echo(req, "dian_report")
    out.update(
        {
            "dian_report_status": status,
            "dian_report_id": f"DIAN-{req.transaction_id}",
            "dian_report_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/notify/email")
def notify(req: NotifyRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "NOTIFICATION_SERVICE_DOWN",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )
    ok = not bool(req.force_reject)
    out = build_echo(req, "notification")
    out.update(
        {
            "notification_status": "SENT" if ok else "FAILED",
            "notification_channel": req.channel,
            "notification_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out
