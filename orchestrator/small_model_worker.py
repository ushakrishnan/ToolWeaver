"""
Small Model Workers - Uses efficient local models (Phi-3, Llama) for specific tasks.

This module provides workers that use small, specialized language models for
tasks like text classification, extraction, and parsing where large models
are overkill. Supports both local inference and cloud endpoints.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Literal
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Optional imports for different backends
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests package not installed")

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
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
        model_name: str = None
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
    
    def _init_transformers(self):
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
        
        hf_model = model_map.get(self.model_name, self.model_name)
        
        self.tokenizer = AutoTokenizer.from_pretrained(hf_model, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            hf_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True
        )
        
        logger.info(f"Model loaded on {'GPU' if torch.cuda.is_available() else 'CPU'}")
    
    def _init_ollama(self):
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
    
    def _init_azure(self):
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
        system_prompt: Optional[str] = None,
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
        system_prompt: Optional[str],
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
        def _infer():
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
            
            return response
        
        return await asyncio.to_thread(_infer)
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
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
        
        def _request():
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        
        return await asyncio.to_thread(_request)
    
    async def _generate_azure(
        self,
        prompt: str,
        system_prompt: Optional[str],
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
            from azure.core.credentials import AccessToken
            
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"
        else:
            # Use API key
            headers["api-key"] = self.azure_key
        
        def _request():
            # Try chat/completions endpoint (OpenAI format)
            endpoint = self.azure_endpoint.rstrip('/')
            if not endpoint.endswith('/chat/completions'):
                endpoint = f"{endpoint}/chat/completions"
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        
        return await asyncio.to_thread(_request)
    
    async def parse_line_items(self, ocr_text: str) -> List[Dict[str, Any]]:
        """
        Parse receipt OCR text into structured line items using small model.
        
        Args:
            ocr_text: Raw text from OCR
            
        Returns:
            List of line items with description, quantity, price, total
        """
        system_prompt = """You are a receipt parser. Extract line items from receipt text.
Output valid JSON array only, no explanations.

Format:
[
  {"description": "item name", "quantity": 1, "unit_price": 2.50, "total": 2.50},
  ...
]

If no items found, return empty array []."""
        
        prompt = f"""Receipt text:
{ocr_text}

Extract all line items as JSON array:"""
        
        response = await self.generate(prompt, system_prompt, max_tokens=1024, temperature=0.1)
        
        # Extract JSON from response
        try:
            # Try to find JSON array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                items = json.loads(json_str)
                logger.info(f"Parsed {len(items)} line items with small model")
                return items
            else:
                logger.warning("No JSON array found in response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse line items JSON: {e}")
            logger.debug(f"Response was: {response}")
            return []
    
    async def categorize_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categorize items into expense categories using small model.
        
        Args:
            items: List of items to categorize
            
        Returns:
            Items with added 'category' field
        """
        system_prompt = """You are an expense categorizer. Assign categories to items.
Categories: food, beverage, household, health, other
Output valid JSON array only, with original fields plus "category"."""
        
        items_json = json.dumps(items, indent=2)
        prompt = f"""Items:
{items_json}

Add "category" field to each item and return complete JSON array:"""
        
        response = await self.generate(prompt, system_prompt, max_tokens=2048, temperature=0.1)
        
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                categorized = json.loads(json_str)
                logger.info(f"Categorized {len(categorized)} items with small model")
                return categorized
            else:
                logger.warning("No JSON array found in categorization response")
                return items
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse categorization JSON: {e}")
            logger.debug(f"Response was: {response}")
            return items
