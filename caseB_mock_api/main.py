from __future__ import annotations

import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

APP_NAME = "caseB-mock-services"
VERSION = "1.0.0"


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


MIN_DELAY_MS = _int_env("MIN_DELAY_MS", 150)
MAX_DELAY_MS = _int_env("MAX_DELAY_MS", 900)
DEFAULT_JITTER_MS = _int_env("DEFAULT_JITTER_MS", 250)
DEFAULT_FAIL_RATE = _float_env("FAIL_RATE", 0.0)

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
    base = delay_ms if delay_ms is not None else random.randint(MIN_DELAY_MS, MAX_DELAY_MS)
    jitter_cap = DEFAULT_JITTER_MS if jitter_ms is None else jitter_ms
    jitter = random.randint(0, max(0, jitter_cap)) if jitter_cap > 0 else 0
    return max(0, base + jitter)



def should_fail(force_error: Optional[bool], fail_rate: Optional[float]) -> bool:
    if force_error:
        return True
    rate = DEFAULT_FAIL_RATE if fail_rate is None else max(0.0, min(1.0, fail_rate))
    return random.random() < rate


class BaseCaseBRequest(BaseModel):
    transaction_id: str = Field(..., description="Correlation id used by the n8n workflow")
    citizen_id: str = Field(..., description="Citizen/user identifier used by the scenario")
    document_number: str = Field(..., description="Document number to validate identity")
    incident_description: str = Field(..., description="Complaint summary or incident description")
    incident_address: str = Field(..., description="Address or textual location of the incident")
    incident_category: str = Field("GENERAL", description="Initial complaint category")
    municipality_code: Optional[str] = Field(None, description="Optional municipality or territorial code")
    delay_ms: Optional[int] = Field(None, ge=0, description="Fixed base delay in ms for this call")
    jitter_ms: Optional[int] = Field(None, ge=0, description="Random jitter (0..jitter_ms)")
    fail_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of technical failure")
    force_error: Optional[bool] = Field(False, description="If true, force a technical failure (5xx)")


class AuthRequest(BaseCaseBRequest):
    requested_scope: str = Field("denuncia.write denuncia.read", description="OAuth2/OIDC scope requested")
    force_reject: Optional[bool] = Field(False, description="If true, the authentication is denied")


class IdentityVerifyRequest(BaseCaseBRequest):
    auth_token: str = Field(..., description="Bearer token or session token from ID·Gob")
    verification_mode: str = Field("document", description="Verification mode: document or biometric")
    force_invalid_identity: Optional[bool] = Field(False, description="If true, identity validation fails")


class PoliceClassifyRequest(BaseCaseBRequest):
    auth_token: str = Field(..., description="Validated session token")
    identity_valid: bool = Field(True, description="Identity validation result from previous step")
    force_reject: Optional[bool] = Field(False, description="If true, police intake/classification rejects the case")


class FiscaliaRegisterRequest(BaseCaseBRequest):
    auth_token: str = Field(..., description="Validated session token")
    identity_valid: bool = Field(True, description="Identity validation result")
    offense_code: str = Field(..., description="Offense code classified by police")
    police_case_reference: str = Field(..., description="Reference generated during police intake")
    territorial_uri: Optional[str] = Field(None, description="Territorial URI or geocoding result")
    force_reject: Optional[bool] = Field(False, description="If true, fiscalia registration is rejected")


class GeorefRequest(BaseCaseBRequest):
    force_reject: Optional[bool] = Field(False, description="If true, geocoding cannot normalize the location")


class NotifyRequest(BaseCaseBRequest):
    channel: str = Field("EMAIL", description="Notification channel")
    noticia_criminal_number: Optional[str] = Field(None, description="Formal criminal report number")
    radicado_id: Optional[str] = Field(None, description="Institutional filing identifier")
    force_reject: Optional[bool] = Field(False, description="If true, notification fails")



def build_echo(payload: BaseCaseBRequest, service: str) -> Dict[str, Any]:
    return {
        "service": service,
        "transaction_id": payload.transaction_id,
        "citizen_id": payload.citizen_id,
        "document_number": payload.document_number,
        "incident_category": payload.incident_category,
    }



def build_meta(
    payload: BaseCaseBRequest,
    simulated_delay_ms: int,
    x_correlation_id: Optional[str],
    started_at: float,
) -> Dict[str, Any]:
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


@app.post("/id-gob/auth")
def id_gob_auth(req: AuthRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ID_GOB_UNAVAILABLE",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    authenticated = not bool(req.force_reject)
    out = build_echo(req, "id_gob_auth")
    out.update(
        {
            "auth_status": "AUTHENTICATED" if authenticated else "DENIED",
            "auth_provider": "GOV.CO_ID_GOB",
            "token_type": "Bearer",
            "auth_token": f"tok-{req.transaction_id}" if authenticated else "",
            "scope": req.requested_scope,
            "auth_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/registraduria/verify-identity")
def registraduria_verify_identity(
    req: IdentityVerifyRequest,
    x_correlation_id: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "REGISTRADURIA_TIMEOUT",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    identity_valid = not bool(req.force_invalid_identity)
    out = build_echo(req, "registraduria_identity")
    out.update(
        {
            "identity_valid": identity_valid,
            "identity_status": "VALID" if identity_valid else "INVALID",
            "verification_mode": req.verification_mode,
            "registraduria_reference": f"REG-{req.transaction_id}",
            "verification_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/policia/classify")
def policia_classify(req: PoliceClassifyRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=502,
            detail={
                "error": "POLICIA_UPSTREAM_ERROR",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    if not req.identity_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "IDENTITY_NOT_VALIDATED",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    accepted = not bool(req.force_reject)
    offense_catalog = {
        "HURTO": "HURTO_SIMPLE",
        "VIOLENCIA": "VIOLENCIA_INTRAFAMILIAR",
        "CIBERDELITO": "ACCESO_ABUSIVO_A_SISTEMA",
        "GENERAL": "OTRO_HECHO_PUNIBLE",
    }
    offense_code = offense_catalog.get(req.incident_category.upper(), "OTRO_HECHO_PUNIBLE")
    out = build_echo(req, "policia_intake")
    out.update(
        {
            "police_status": "CLASSIFIED" if accepted else "REJECTED",
            "offense_code": offense_code,
            "offense_description": offense_code.replace("_", " "),
            "routing_target": "FISCALIA_GENERAL",
            "police_case_reference": f"SPOA-POL-{req.transaction_id}",
            "classification_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/fiscalia/register")
def fiscalia_register(req: FiscaliaRegisterRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FISCALIA_GATEWAY_TIMEOUT",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    if not req.identity_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "IDENTITY_REQUIRED",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    registered = not bool(req.force_reject)
    municipality = req.municipality_code or "11001"
    out = build_echo(req, "fiscalia_registration")
    out.update(
        {
            "fiscalia_status": "REGISTERED" if registered else "REJECTED",
            "noticia_criminal_number": f"NC-{municipality}-{req.transaction_id}",
            "radicado_id": f"RAD-{req.transaction_id}",
            "jurisdiction_code": municipality,
            "territorial_uri": req.territorial_uri or f"uri://territorio/{municipality}",
            "police_case_reference": req.police_case_reference,
            "registration_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/georef/geocode")
def georef_geocode(req: GeorefRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    t0 = time.perf_counter()
    simulated_delay_ms = compute_delay_ms(req.delay_ms, req.jitter_ms)
    sleep_ms(simulated_delay_ms)
    if should_fail(req.force_error, req.fail_rate):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "GEOREF_SERVICE_UNAVAILABLE",
                "correlation_id": x_correlation_id,
                "simulated_delay_ms": simulated_delay_ms,
            },
        )

    geocoded = not bool(req.force_reject)
    municipality = req.municipality_code or "11001"
    out = build_echo(req, "georef")
    out.update(
        {
            "georef_status": "GEOCODED" if geocoded else "FAILED",
            "normalized_address": req.incident_address.upper(),
            "territorial_uri": f"uri://territorio/{municipality}/{req.transaction_id}" if geocoded else "",
            "geocode_provider": "IGAC_CATASTRO_GOOGLE_ESRI",
            "geocode_confidence": 0.97 if geocoded else 0.0,
            "latitude": 4.60971 if geocoded else None,
            "longitude": -74.08175 if geocoded else None,
            "geocode_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out


@app.post("/notify/email")
def notify_email(req: NotifyRequest, x_correlation_id: Optional[str] = Header(default=None)) -> Dict[str, Any]:
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

    delivered = not bool(req.force_reject)
    out = build_echo(req, "notification")
    out.update(
        {
            "notification_status": "SENT" if delivered else "FAILED",
            "notification_channel": req.channel,
            "delivery_reference": f"MAIL-{req.transaction_id}",
            "noticia_criminal_number": req.noticia_criminal_number,
            "radicado_id": req.radicado_id,
            "notification_time": now_iso(),
        }
    )
    out.update(build_meta(req, simulated_delay_ms, x_correlation_id, t0))
    return out
