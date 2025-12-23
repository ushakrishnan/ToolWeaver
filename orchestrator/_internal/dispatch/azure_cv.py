from __future__ import annotations

from typing import Any

# This module provides a local wrapper around Azure CV imports so that:
# - Runtime gracefully degrades when Azure SDK isn't installed
# - Type checking can rely on a stable module surface (via azure_cv.pyi)

AZURE_CV_AVAILABLE: bool

try:
    from dotenv import load_dotenv
    load_dotenv()

    from azure.ai.vision.imageanalysis import ImageAnalysisClient  # type: ignore
    from azure.ai.vision.imageanalysis.models import VisualFeatures  # type: ignore
    from azure.core.credentials import AzureKeyCredential  # type: ignore
    from azure.identity import DefaultAzureCredential  # type: ignore

    AZURE_CV_AVAILABLE = True
except Exception:  # noqa: BLE001 - any failure means unavailable
    # Fallback runtime placeholders when Azure SDK is not present.
    ImageAnalysisClient = Any  # type: ignore[assignment]
    VisualFeatures = Any  # type: ignore[assignment]
    AzureKeyCredential = Any  # type: ignore[assignment]
    DefaultAzureCredential = Any  # type: ignore[assignment]
    AZURE_CV_AVAILABLE = False
