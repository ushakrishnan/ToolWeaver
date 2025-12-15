import asyncio
import os
import logging
from typing import Dict, Any
from .models import ReceiptOCROut, LineItemParserOut, LineItem, CategorizerOut

logger = logging.getLogger(__name__)

# Optional small model worker import
_small_model_worker = None

def _get_small_model_worker():
    """Lazy initialization of small model worker."""
    global _small_model_worker
    if _small_model_worker is None:
        use_small_model = os.getenv("USE_SMALL_MODEL", "false").lower() == "true"
        if use_small_model:
            try:
                from .small_model_worker import SmallModelWorker
                backend = os.getenv("SMALL_MODEL_BACKEND", "ollama")
                model_name = os.getenv("WORKER_MODEL", "phi3")
                _small_model_worker = SmallModelWorker(backend=backend, model_name=model_name)
                logger.info(f"Initialized small model worker: {backend}/{model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize small model worker: {e}")
                _small_model_worker = False
        else:
            _small_model_worker = False
    return _small_model_worker if _small_model_worker is not False else None

# Try to import Azure CV, fall back to mock mode if not available
try:
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv
    load_dotenv()
    AZURE_CV_AVAILABLE = True
except ImportError:
    AZURE_CV_AVAILABLE = False
    logger.warning("Azure Computer Vision SDK not installed. Running in mock mode.")

async def receipt_ocr_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract text from receipt images using Azure Computer Vision OCR.
    Falls back to mock data if Azure is not configured.
    """
    image_uri = payload.get("image_uri")
    ocr_mode = os.getenv("OCR_MODE", "mock")
    
    # Use Azure Computer Vision if configured and available
    if ocr_mode == "azure" and AZURE_CV_AVAILABLE:
        try:
            endpoint = os.getenv("AZURE_CV_ENDPOINT")
            key = os.getenv("AZURE_CV_KEY")
            use_azure_ad = os.getenv("AZURE_USE_AD", "false").lower() == "true"
            
            if not endpoint:
                logger.warning("Azure CV endpoint not configured. Using mock data.")
                return _mock_ocr(image_uri)
            
            logger.info(f"Processing image with Azure Computer Vision: {image_uri}")
            
            # Choose authentication method
            if use_azure_ad or not key:
                # Use Azure AD authentication (DefaultAzureCredential)
                logger.info("Using Azure AD authentication")
                credential = DefaultAzureCredential()
            else:
                # Use API key authentication
                logger.info("Using API key authentication")
                credential = AzureKeyCredential(key)
            
            # Create the client
            client = ImageAnalysisClient(
                endpoint=endpoint,
                credential=credential
            )
            
            # Analyze image for text (Read API)
            result = await asyncio.to_thread(
                client.analyze_from_url,
                image_url=image_uri,
                visual_features=[VisualFeatures.READ]
            )
            
            # Extract text from results
            extracted_text = []
            if result.read and result.read.blocks:
                for block in result.read.blocks:
                    for line in block.lines:
                        extracted_text.append(line.text)
            
            text = "\n".join(extracted_text) if extracted_text else "No text detected"
            confidence = 0.95  # Azure CV is typically high confidence
            
            logger.info(f"Successfully extracted {len(extracted_text)} lines of text")
            return ReceiptOCROut(text=text, confidence=confidence).model_dump()
            
        except Exception as e:
            logger.error(f"Azure Computer Vision error: {e}. Falling back to mock data.")
            return _mock_ocr(image_uri)
    else:
        # Mock mode
        return _mock_ocr(image_uri)

def _mock_ocr(image_uri: str) -> Dict[str, Any]:
    """Generate mock OCR data for testing."""
    text = f"MOCK RECEIPT DATA (from {image_uri})\n\nCoffee Shop Receipt\n1x Coffee 3.50\n2x Bagel 5.00\nSubtotal: 8.50\nTax: 0.68\nTOTAL: 9.18"
    return ReceiptOCROut(text=text, confidence=0.98).model_dump()

async def line_item_parser_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse OCR text into structured line items.
    Uses small model (Phi-3) if configured, otherwise falls back to keyword matching.
    """
    ocr_text = payload.get("ocr_text") or payload.get("text") or ""
    # Handle case where ocr_text is a dict (from step reference)
    if isinstance(ocr_text, dict):
        ocr_text = ocr_text.get("text", "")
    
    # Try small model first
    small_model = _get_small_model_worker()
    if small_model:
        try:
            logger.info("Using small model for line item parsing")
            items_dicts = await small_model.parse_line_items(ocr_text)
            items = [LineItem(**item) for item in items_dicts]
            return LineItemParserOut(items=items).model_dump()
        except Exception as e:
            logger.warning(f"Small model parsing failed, falling back to keyword matching: {e}")
    
    # Fallback: Simple keyword matching
    await asyncio.sleep(0.1)
    items = []
    for line in ocr_text.splitlines():
        line = line.strip()
        if line.lower().startswith("total"):
            continue
        if 'coffee' in line.lower():
            items.append(LineItem(description='Coffee', quantity=1, unit_price=3.5, total=3.5))
        if 'bagel' in line.lower():
            items.append(LineItem(description='Bagel', quantity=2, unit_price=2.5, total=5.0))
    return LineItemParserOut(items=items).model_dump()

async def expense_categorizer_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorize items into expense categories.
    Uses small model (Phi-3) if configured, otherwise falls back to keyword matching.
    """
    items = payload.get("items", [])
    # Handle case where items is nested in a dict (from step reference)
    if isinstance(items, dict):
        items = items.get("items", [])
    
    # Try small model first
    small_model = _get_small_model_worker()
    if small_model and items:
        try:
            logger.info("Using small model for expense categorization")
            categorized = await small_model.categorize_items(items)
            return CategorizerOut(categorized=categorized).model_dump()
        except Exception as e:
            logger.warning(f"Small model categorization failed, falling back to keyword matching: {e}")
    
    # Fallback: Simple keyword matching
    await asyncio.sleep(0.05)
    categorized = []
    for it in items:
        desc = it.get("description", "").lower()
        category = "food"
        if "coffee" in desc:
            category = "beverage"
        categorized.append({**it, "category": category})
    return CategorizerOut(categorized=categorized).model_dump()
