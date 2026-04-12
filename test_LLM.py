"""Test HF Router with correct model paths."""
import os
from openai import OpenAI

API_KEY = os.environ.get("HF_TOKEN", "NOT SET")
print(f"Token: {API_KEY[:15]}...")

attempts = [
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "microsoft/Phi-3-mini-4k-instruct",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "google/gemma-2-2b-it",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "Qwen/Qwen2.5-72B-Instruct",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    },
    {
        "url": "https://router.huggingface.co/hf-inference/v1",
        "model": "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    },
    {
        "url": "https://router.huggingface.co/novita/v3/openai/v1",
        "model": "meta-llama/llama-3.1-8b-instruct",
    },
    {
        "url": "https://router.huggingface.co/nebius/v1",
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    },
    {
        "url": "https://router.huggingface.co/cerebras/v1",
        "model": "llama3.1-8b",
    },
    {
        "url": "https://router.huggingface.co/sambanova/v1",
        "model": "Meta-Llama-3.1-8B-Instruct",
    },
]

for i, attempt in enumerate(attempts, 1):
    url = attempt["url"]
    model = attempt["model"]
    print(f"\n--- Attempt {i}/{len(attempts)} ---")
    print(f"  URL:   {url}")
    print(f"  Model: {model}")

    client = OpenAI(base_url=url, api_key=API_KEY)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ],
            max_tokens=10,
            timeout=30,
        )
        answer = response.choices[0].message.content
        print(f"  SUCCESS! Response: {answer}")
        print(f"\n{'='*55}")
        print(f"  WORKING CONFIGURATION FOUND!")
        print(f"{'='*55}")
        print(f"\n  Run these in your cmd terminal:")
        print(f"")
        print(f"  set API_BASE_URL={url}")
        print(f"  set MODEL_NAME={model}")
        print(f"")
        print(f"  Then run:")
        print(f"  python inference.py")
        exit()

    except Exception as e:
        err = str(e)[:150]
        print(f"  FAILED: {err}")

print(f"\n{'='*55}")
print("  ALL FAILED")
print(f"{'='*55}")
print("\n  Last resort options:")
print("  1. Go to https://huggingface.co/settings/tokens")
print("     Delete ALL tokens")
print("     Create brand new token with ALL permissions")
print("  2. Try: pip install huggingface-hub")
print("     Then: huggingface-cli login")
print("     Paste your token when asked")
print("  3. Ask competition organizers for API details")