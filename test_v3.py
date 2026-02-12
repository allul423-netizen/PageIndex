from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

print(f"Testing Connection to: {base_url}")
print(f"Using Model: {model}")
# print(f"API Key: {api_key[:5]}...{api_key[-5:]}")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

print("\nSending request...")
try:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hello, please reply with 'Connection Successful' if you receive this."}],
        temperature=0.7
    )
    print("\nResponse received:")
    print(response.choices[0].message.content)
    print("\nTest passed!")
except Exception as e:
    print(f"\nError occurred: {e}")
    print("Test failed.")
