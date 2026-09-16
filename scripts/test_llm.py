import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.reasoning.llm_client import get_llm

llm = get_llm()
print(f"Provider: {llm.provider}")
print(f"Model:    {llm.model}\n")

result = llm.chat(
    system_prompt="You are a helpful assistant. Be concise.",
    user_message="In one sentence, why does soil organic carbon matter for biodiversity?",
    max_tokens=200,
)

print("CONTENT:")
print(result["content"])
print(f"\nREASONING: {result['reasoning'][:200] if result['reasoning'] else 'none'}...")
print(f"MODEL: {result['model']}")
print(f"TOKENS: {result['usage']}")