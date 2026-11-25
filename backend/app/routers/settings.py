import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
import httpx

from app.config import settings
from app.schemas import SettingsResponse, SettingsUpdateRequest, ApiTestResponse
from app.services.job_manager import job_manager

logger = logging.getLogger("voicescribe.routers.settings")
router = APIRouter(prefix="/api/settings", tags=["settings"])


def update_env_file(key: str, value: str, env_path: Optional[str] = None):
    """
    Safely updates or appends a KEY=VALUE entry in backend/.env
    so configurations persist across server restarts.
    """
    if not env_path:
        # Default to backend/.env
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(base_dir, ".env")

    lines = []
    key_found = False
    prefix = f"{key}="

    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(prefix) or stripped.startswith(f"# {prefix}"):
                    lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    lines.append(line)

    if not key_found:
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info(f"[Settings] Saved '{key}' to {env_path}")


@router.get("", response_model=SettingsResponse)
def get_settings():
    """
    Returns the current provider configuration, active mode, and provider readiness.
    Masks secret API keys for secure frontend display.
    """
    key = settings.effective_api_key
    masked_key = ""
    if key:
        if len(key) > 8:
            masked_key = f"{key[:4]}...{key[-4:]}"
        else:
            masked_key = "***"

    local_ready = bool(job_manager.local_provider and job_manager.local_provider.is_ready())
    api_ready = bool(job_manager.api_provider and job_manager.api_provider.is_ready())

    active_format = None
    if job_manager.api_provider:
        active_format = job_manager.api_provider.get_active_response_format()
    elif getattr(settings, "TRANSCRIPTION_RESPONSE_FORMAT", None):
        active_format = settings.TRANSCRIPTION_RESPONSE_FORMAT

    return SettingsResponse(
        transcription_mode=settings.TRANSCRIPTION_MODE,
        api_key_configured=bool(key),
        api_key_masked=masked_key,
        api_url=settings.TRANSCRIPTION_API_URL,
        api_model=settings.TRANSCRIPTION_API_MODEL,
        response_format=active_format,
        local_model=settings.WHISPER_MODEL,
        device=settings.DEVICE,
        local_ready=local_ready,
        api_ready=api_ready
    )


@router.post("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdateRequest):
    """
    Updates transcription settings (selecting 'local' or 'api' mode, API key, endpoint, model, response_format).
    Persists updates to backend/.env and updates active runtime providers.
    """
    # 1. Update transcription mode
    if payload.transcription_mode is not None:
        mode = payload.transcription_mode.lower().strip()
        if mode not in ("local", "api"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transcription_mode. Must be 'local' or 'api'."
            )
        settings.TRANSCRIPTION_MODE = mode
        try:
            update_env_file("TRANSCRIPTION_MODE", mode)
        except Exception as e:
            logger.warning(f"Failed to persist TRANSCRIPTION_MODE to .env: {e}")

    # 2. Update API Key
    if payload.api_key is not None:
        key_val = payload.api_key.strip()
        settings.TRANSCRIPTION_API_KEY = key_val or None
        if job_manager.api_provider:
            job_manager.api_provider.set_api_key(key_val)
        try:
            update_env_file("TRANSCRIPTION_API_KEY", key_val)
        except Exception as e:
            logger.warning(f"Failed to persist TRANSCRIPTION_API_KEY to .env: {e}")

    # 3. Update API Endpoint URL
    if payload.api_url is not None and payload.api_url.strip():
        url_val = payload.api_url.strip()
        settings.TRANSCRIPTION_API_URL = url_val
        if job_manager.api_provider:
            job_manager.api_provider.set_endpoint(
                url_val, 
                settings.TRANSCRIPTION_API_MODEL,
                getattr(settings, "TRANSCRIPTION_RESPONSE_FORMAT", None)
            )
        try:
            update_env_file("TRANSCRIPTION_API_URL", url_val)
        except Exception as e:
            logger.warning(f"Failed to persist TRANSCRIPTION_API_URL to .env: {e}")

    # 4. Update API Model
    if payload.api_model is not None and payload.api_model.strip():
        model_val = payload.api_model.strip()
        settings.TRANSCRIPTION_API_MODEL = model_val
        if job_manager.api_provider:
            job_manager.api_provider.set_endpoint(
                settings.TRANSCRIPTION_API_URL, 
                model_val,
                getattr(settings, "TRANSCRIPTION_RESPONSE_FORMAT", None)
            )
        try:
            update_env_file("TRANSCRIPTION_API_MODEL", model_val)
        except Exception as e:
            logger.warning(f"Failed to persist TRANSCRIPTION_API_MODEL to .env: {e}")

    # 5. Update Response Format (if specified)
    if payload.response_format is not None:
        fmt_val = payload.response_format.strip() or None
        settings.TRANSCRIPTION_RESPONSE_FORMAT = fmt_val
        if job_manager.api_provider:
            job_manager.api_provider.response_format = fmt_val
        if fmt_val:
            try:
                update_env_file("TRANSCRIPTION_RESPONSE_FORMAT", fmt_val)
            except Exception as e:
                logger.warning(f"Failed to persist TRANSCRIPTION_RESPONSE_FORMAT to .env: {e}")

    logger.info(
        f"[Settings] Settings updated: mode={settings.TRANSCRIPTION_MODE}, "
        f"model={settings.TRANSCRIPTION_API_MODEL}, "
        f"api_key_set={bool(settings.effective_api_key)}, "
        f"api_url={settings.TRANSCRIPTION_API_URL}"
    )

    return get_settings()


@router.post("/test-api", response_model=ApiTestResponse)
def test_api_key(payload: Optional[SettingsUpdateRequest] = None):
    """
    Validates that the provided or configured API key can authenticate
    against the transcription endpoint with a compatible response_format.
    """
    test_key = (payload and payload.api_key and payload.api_key.strip()) or settings.effective_api_key
    if not test_key:
        return ApiTestResponse(
            success=False,
            message="No API key provided or configured. Enter a key to test."
        )

    endpoint = (payload and payload.api_url and payload.api_url.strip()) or settings.TRANSCRIPTION_API_URL
    model = (payload and payload.api_model and payload.api_model.strip()) or settings.TRANSCRIPTION_API_MODEL
    req_format = payload.response_format if payload else None

    # Check if requested format is compatible with the model
    try:
        from app.services.providers.api_whisper import ApiTranscriptionProvider
        compatible_format = ApiTranscriptionProvider.select_response_format(model, req_format)
    except ValueError as ve:
        return ApiTestResponse(
            success=False,
            message=str(ve)
        )

    # Make a quick test request with empty audio to test authentication
    try:
        headers = {"Authorization": f"Bearer {test_key}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                endpoint,
                headers=headers,
                data={
                    "model": model,
                    "response_format": compatible_format
                }
            )

            # If 401 Unauthorized, key is definitely invalid
            if resp.status_code == 401:
                return ApiTestResponse(
                    success=False,
                    message="Authentication failed (HTTP 401 Unauthorized): Invalid API Key."
                )
            elif resp.status_code == 404:
                return ApiTestResponse(
                    success=False,
                    message=f"Endpoint or model not found (HTTP 404): Check URL '{endpoint}'."
                )
            elif resp.status_code == 429:
                return ApiTestResponse(
                    success=False,
                    message="API key is valid, but your account exceeded quota / rate limits (HTTP 429)."
                )
            elif resp.status_code == 400:
                err_text = resp.text
                try:
                    err_json = resp.json()
                    if "error" in err_json and isinstance(err_json["error"], dict):
                        err_text = err_json["error"].get("message", err_text)
                except Exception:
                    pass

                # If format incompatibility error
                if "response_format" in err_text.lower() and ("not compatible" in err_text.lower() or "compatible" in err_text.lower()):
                    return ApiTestResponse(
                        success=False,
                        message=f"Model format incompatibility: {err_text}"
                    )

                if "model" in err_text.lower() and ("does not exist" in err_text.lower() or "not found" in err_text.lower()):
                    return ApiTestResponse(
                        success=False,
                        message=f"Model error: {err_text}"
                    )

                # 400 is expected because we didn't send a file! But 400 means auth passed!
                return ApiTestResponse(
                    success=True,
                    message=f"API connection verified successfully for model '{model}' (format: {compatible_format})! Server accepted authentication."
                )
            elif resp.status_code < 500:
                return ApiTestResponse(
                    success=True,
                    message=f"API connection successful (HTTP {resp.status_code}). Format: {compatible_format}."
                )
            else:
                return ApiTestResponse(
                    success=False,
                    message=f"Endpoint returned server error (HTTP {resp.status_code})."
                )

    except httpx.TimeoutException:
        return ApiTestResponse(
            success=False,
            message="Connection timed out while trying to reach the API endpoint."
        )
    except Exception as e:
        return ApiTestResponse(
            success=False,
            message=f"Connection error: {str(e)}"
        )
