"""
Small Model Workers - Uses efficient local models (Phi-3, Llama) for specific tasks.

This module provides workers that use small, specialized language models for
tasks like text classification, extraction, and parsing where large models
are overkill. Supports both local inference and cloud endpoints.
"""

import json
import logging
import os
from collections.abc import Callable
from typing import Any, Literal

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# JSON repair utility
def _repair_json(text: str) -> str:
    """Attempt to repair common JSON formatting issues."""
    import re
    # Remove control characters (keep standard whitespace)
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    # Fix common issues
    text = text.replace('\n', ' ').replace('\r', '')
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text

# Optional imports for different backends
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests package not installed")

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers/torch not installed. Install with: pip install transformers torch")


class SmallModelWorker:
    """
    Worker that uses small language models (Phi-3, Llama 3.2, etc.) for
    specific tasks like text classification, extraction, and parsing.

    Supports multiple backends:
    - Local inference via transformers (CPU/GPU)
    - Ollama API (local server)
    - Azure AI/OpenAI endpoints (hosted small models)
    """

    def __init__(
        self,
        backend: Literal["transformers", "ollama", "azure"] = "ollama",
            model_name: str | None = None
    ):
        """
        Initialize the small model worker.

        Args:
            backend: "transformers" for local, "ollama" for Ollama server, "azure" for cloud
            model_name: Model to use (e.g., "phi3", "llama3.2", "microsoft/Phi-3-mini-4k-instruct")
        """
        self.backend = backend
        self.model_name = model_name or os.getenv("WORKER_MODEL", "phi3")

        if self.backend == "transformers":
            self._init_transformers()
        elif self.backend == "ollama":
            self._init_ollama()
        elif self.backend == "azure":
            self._init_azure()
        else:
            raise ValueError(f"Unknown backend: {backend}")

        logger.info(f"Initialized SmallModelWorker with {backend} backend ({self.model_name})")

    def _init_transformers(self) -> None:
        """Initialize local transformers model."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers package not installed")

        logger.info(f"Loading model {self.model_name} locally...")

        # Map common names to HuggingFace model IDs
        model_map = {
            "phi3": "microsoft/Phi-3-mini-4k-instruct",
            "phi3.5": "microsoft/Phi-3.5-mini-instruct",
            "llama3.2": "meta-llama/Llama-3.2-3B-Instruct"
        }

        model_key = self.model_name or "phi3"
        hf_model = model_map.get(model_key, model_key)

        self.tokenizer = AutoTokenizer.from_pretrained(hf_model, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            hf_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True
        )

        logger.info(f"Model loaded on {'GPU' if torch.cuda.is_available() else 'CPU'}")

    def _init_ollama(self) -> None:
        """Initialize Ollama API client."""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests package not installed")

        self.ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

        # Test connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info(f"Connected to Ollama at {self.ollama_url}")
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")

    def _init_azure(self) -> None:
        """Initialize Azure AI endpoint (Azure AI Foundry or Azure OpenAI)."""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests package not installed")

        # Support both Azure AI Foundry and Azure OpenAI endpoints
        self.azure_endpoint = os.getenv("AZURE_SMALL_MODEL_ENDPOINT")
        self.azure_key = os.getenv("AZURE_SMALL_MODEL_KEY")

        # Optional: Use Azure AD authentication
        self.use_azure_ad = os.getenv("AZURE_SMALL_MODEL_USE_AD", "false").lower() == "true"

        if not self.azure_endpoint:
            raise ValueError("AZURE_SMALL_MODEL_ENDPOINT required for Azure backend")

        if not self.use_azure_ad and not self.azure_key:
            raise ValueError("AZURE_SMALL_MODEL_KEY required for Azure backend (or set AZURE_SMALL_MODEL_USE_AD=true)")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.1
    ) -> str:
        """
        Generate text using the small model.

        Args:
            prompt: User prompt/question
            system_prompt: Optional system prompt for instruction
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text
        """
        if self.backend == "transformers":
            return await self._generate_transformers(prompt, system_prompt, max_tokens, temperature)
        elif self.backend == "ollama":
            return await self._generate_ollama(prompt, system_prompt, max_tokens, temperature)
        elif self.backend == "azure":
            return await self._generate_azure(prompt, system_prompt, max_tokens, temperature)

    async def _generate_transformers(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using local transformers model."""
        import asyncio

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Format with chat template
        input_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Run inference in thread pool
        def _infer() -> str:
            inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the assistant response
            if "<|assistant|>" in response:
                response = response.split("<|assistant|>")[-1].strip()
            elif "assistant" in response.lower():
                parts = response.split("\n")
                for i, part in enumerate(parts):
                    if "assistant" in part.lower() and i + 1 < len(parts):
                        response = "\n".join(parts[i+1:]).strip()
                        break

            return str(response)

        infer_fn: Callable[[], str] = _infer
        return str(await asyncio.to_thread(infer_fn))

    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Ollama API."""
        import asyncio

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        def _request() -> str:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return str(response.json()["response"])

        return await asyncio.to_thread(_request)

    async def _generate_azure(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Azure AI endpoint (Foundry or OpenAI format)."""
        import asyncio

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # Support both API key and Azure AD authentication
        headers = {"Content-Type": "application/json"}

        if self.use_azure_ad:
            # Use Azure AD token
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"
        else:
            # Use API key
            if self.azure_key is None:
                raise ValueError("Azure API key is required when not using Azure AD")
            headers["api-key"] = self.azure_key

        def _request() -> str:
            # Try chat/completions endpoint (OpenAI format)
            azure_ep = self.azure_endpoint or ""
            endpoint = azure_ep.rstrip('/')
            if not endpoint.endswith('/chat/completions'):
                endpoint = f"{endpoint}/chat/completions"

            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            return str(result)  # Ensure string return

        return await asyncio.to_thread(_request)

    async def parse_line_items(self, ocr_text: str, max_retries: int = 2) -> list[dict[str, Any]]:
        """
        Parse receipt OCR text into structured line items using small model.

        Args:
            ocr_text: Raw text from OCR
            max_retries: Number of retry attempts if JSON parsing fails

        Returns:
            List of line items with description, quantity, price, total
        """
        system_prompt = """You are a JSON-only parser. Return ONLY the JSON array, nothing else.

Extract line items from receipts. Skip totals/tax/subtotals.
Format: [{"description": "Item", "quantity": N, "unit_price": X.XX, "total": Y.YY}]

NO explanations. NO markdown. ONLY the JSON array."""

        prompt = f"""Receipt text:
{ocr_text}

JSON array of line items:"""

        for attempt in range(max_retries + 1):
            try:
                response = await self.generate(prompt, system_prompt, max_tokens=1024, temperature=0.05)

                # Clean up response - remove markdown code blocks if present
                response = response.strip()
                if response.startswith('```'):
                    lines = response.split('\n')
                    response = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
                response = response.strip()

                # Extract JSON array from response - try multiple positions
                start_pos = 0
                while True:
                    start = response.find('[', start_pos)
                    if start < 0:
                        break

                    # Find matching closing bracket
                    bracket_count = 0
                    end = start
                    for i in range(start, len(response)):
                        if response[i] == '[':
                            bracket_count += 1
                        elif response[i] == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end = i + 1
                                break

                    if end > start:
                        try:
                            json_str = response[start:end]
                            json_str = _repair_json(json_str)
                            items = json.loads(json_str)
                            if isinstance(items, list):  # Verify it's actually an array
                                logger.info(f"Parsed {len(items)} line items with small model (attempt {attempt + 1})")
                                return items
                        except json.JSONDecodeError:
                            # Try next array in response
                            start_pos = start + 1
                            continue

                    start_pos = start + 1

                logger.warning(f"No valid JSON array found in response (attempt {attempt + 1})")
                if attempt < max_retries:
                    continue
                return []
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    # Adjust prompt for retry
                    system_prompt += "\n\nIMPORTANT: Ensure output is valid JSON with proper escaping."
                    continue
                else:
                    logger.error(f"Failed to parse line items after {max_retries + 1} attempts")
                    logger.error(f"Final response was: {response[:800]}")
                    return []
            except Exception as e:
                logger.error(f"Unexpected error parsing line items: {e}")
                return []

        return []

    async def categorize_items(self, items: list[dict[str, Any]], max_retries: int = 2) -> list[dict[str, Any]]:
        """
        Categorize items into expense categories using small model.

        Args:
            items: List of items to categorize
            max_retries: Number of retry attempts if JSON parsing fails

        Returns:
            Items with added 'category' field
        """
        if not items:
            return []

        system_prompt = """You are an expense categorizer.

RULES:
1. Output ONLY a valid JSON array - no markdown, no explanations
2. Categories: food, beverage, household, health, other
3. Keep all original fields and add "category" field
4. Use standard ASCII characters only

EXAMPLE:
Input: [{"description": "Coffee", "quantity": 1, "unit_price": 3.50, "total": 3.50}]
Output: [{"description": "Coffee", "quantity": 1, "unit_price": 3.50, "total": 3.50, "category": "beverage"}]"""

        items_json = json.dumps(items, indent=2)
        prompt = f"""Items to categorize:
{items_json}

JSON array with category added:"""

        for attempt in range(max_retries + 1):
            try:
                response = await self.generate(prompt, system_prompt, max_tokens=2048, temperature=0.05)

                # Clean up response - remove markdown code blocks
                response = response.strip()
                if response.startswith('```'):
                    lines = response.split('\n')
                    response = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
                response = response.strip()

                # Extract JSON array
                start = response.find('[')
                end = response.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    json_str = _repair_json(json_str)
                    categorized_raw = json.loads(json_str)
                    # Cast to expected type
                    categorized: list[dict[str, Any]] = categorized_raw if isinstance(categorized_raw, list) else []
                    logger.info(f"Categorized {len(categorized)} items with small model (attempt {attempt + 1})")
                    return categorized
                else:
                    logger.warning(f"No JSON array found in categorization response (attempt {attempt + 1})")
                    if attempt < max_retries:
                        continue
                    return items
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    system_prompt += "\n\nIMPORTANT: Ensure output is valid JSON with proper escaping."
                    continue
                else:
                    logger.error(f"Failed to parse categorization after {max_retries + 1} attempts")
                    logger.debug(f"Final response was: {response[:500]}")
                    return items
            except Exception as e:
                logger.error(f"Unexpected error categorizing items: {e}")
                return items

        return items
