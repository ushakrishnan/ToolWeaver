from typing import Any

AZURE_CV_AVAILABLE: bool

class ImageAnalysisClient:
    def __init__(self, *, endpoint: str, credential: Any) -> None: ...
    def analyze_from_url(self, *, image_url: str, visual_features: list[Any]) -> Any: ...

class VisualFeatures:
    READ: Any

class AzureKeyCredential:
    def __init__(self, key: str) -> None: ...

class DefaultAzureCredential:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
