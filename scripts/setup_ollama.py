#!/usr/bin/env python3
"""Setup script to pull required Ollama models.

This script connects to the Ollama server and pulls the models
needed for DeepThought agents.

Usage:
    python scripts/setup_ollama.py

Prerequisites:
    - Ollama server running (docker compose up -d ollama)
    - Network access to Ollama API
"""

import argparse
import sys
import time
import urllib.error
import urllib.request
import json

# Default models to pull
DEFAULT_MODELS = [
    "llama3.2",      # Lightweight, good for testing (3B params)
    "mistral",       # Good quality/speed balance (7B params)
]

# Optional models (larger, better quality)
OPTIONAL_MODELS = [
    "deepseek-r1",   # Strong reasoning
    "qwen2.5",       # Good multilingual support
]


def check_ollama_health(base_url: str, timeout: int = 5) -> bool:
    """Check if Ollama server is healthy.

    Args:
        base_url: The Ollama server URL.
        timeout: Request timeout in seconds.

    Returns:
        True if server is healthy, False otherwise.
    """
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError):
        return False


def wait_for_ollama(base_url: str, max_wait: int = 60) -> bool:
    """Wait for Ollama server to be ready.

    Args:
        base_url: The Ollama server URL.
        max_wait: Maximum seconds to wait.

    Returns:
        True if server became ready, False if timeout.
    """
    print(f"Waiting for Ollama server at {base_url}...")
    start = time.time()
    while time.time() - start < max_wait:
        if check_ollama_health(base_url):
            print("Ollama server is ready!")
            return True
        time.sleep(2)
        print(".", end="", flush=True)
    print("\nTimeout waiting for Ollama server.")
    return False


def get_installed_models(base_url: str) -> list[str]:
    """Get list of installed models.

    Args:
        base_url: The Ollama server URL.

    Returns:
        List of installed model names.
    """
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return [m["name"].split(":")[0] for m in data.get("models", [])]
    except (urllib.error.URLError, json.JSONDecodeError):
        return []


def pull_model(base_url: str, model: str) -> bool:
    """Pull a model from Ollama.

    Args:
        base_url: The Ollama server URL.
        model: The model name to pull.

    Returns:
        True if successful, False otherwise.
    """
    print(f"\nPulling model: {model}")
    print("This may take a while depending on model size and connection speed...")

    try:
        data = json.dumps({"name": model, "stream": False}).encode()
        req = urllib.request.Request(
            f"{base_url}/api/pull",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Long timeout for large model downloads
        with urllib.request.urlopen(req, timeout=1800) as response:
            result = json.loads(response.read().decode())
            if result.get("status") == "success":
                print(f"Successfully pulled: {model}")
                return True
            else:
                print(f"Pull completed with status: {result}")
                return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error pulling {model}: {e}")
        return False
    except urllib.error.URLError as e:
        print(f"URL Error pulling {model}: {e}")
        return False
    except Exception as e:
        print(f"Error pulling {model}: {e}")
        return False


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Setup Ollama models for DeepThought"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Also pull optional larger models",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Specific models to pull (overrides defaults)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    # Wait for Ollama to be ready
    if not wait_for_ollama(base_url):
        print("\nError: Ollama server is not available.")
        print("Make sure to start it with: docker compose up -d ollama")
        return 1

    # Determine which models to pull
    if args.models:
        models = args.models
    else:
        models = DEFAULT_MODELS.copy()
        if args.include_optional:
            models.extend(OPTIONAL_MODELS)

    # Check already installed models
    installed = get_installed_models(base_url)
    print(f"\nAlready installed models: {installed or '(none)'}")

    # Pull missing models
    to_pull = [m for m in models if m not in installed]
    if not to_pull:
        print("\nAll requested models are already installed!")
        return 0

    print(f"\nModels to pull: {to_pull}")

    # Pull each model
    success_count = 0
    for model in to_pull:
        if pull_model(base_url, model):
            success_count += 1

    # Summary
    print(f"\n{'='*50}")
    print(f"Successfully pulled: {success_count}/{len(to_pull)} models")

    if success_count == len(to_pull):
        print("\nSetup complete! You can now use these models with DeepThought.")
        print("\nTo test, run:")
        print(f'  curl {base_url}/api/generate -d \'{{"model": "{models[0]}", "prompt": "Hello!"}}\'')
        return 0
    else:
        print("\nSome models failed to pull. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
