import os
import sys
from openai import OpenAI

from openai import RateLimitError, APIConnectionError, AuthenticationError
from dotenv import load_dotenv

load_dotenv()

def execute_dynamic_cloud_assistant():
    # Retrieve your GitHub token from the environment
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        print("\n[FAIL] Configuration Exception: Valid 'GITHUB_TOKEN' missing from your local .env file.", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize OpenAI client pointed at GitHub Models endpoint
        client = OpenAI(
            base_url="https://api.githubcopilot.com",
            api_key=github_token
        )

        print("=" * 65)
        print("         GITHUB MODELS INTEGRATION ACTIVE [DYNAMIC INTERFACE]    ")
        print("=" * 65)
        print("[*] Target Deployment Endpoint: https://models.inference.ai.azure.com")
        print("[*] Target Computational Engine: gpt-4o-mini")
        print("[*] Instructions: Type your question below and press Enter.")
        print("[*] Operations: Type 'exit' to terminate the current execution loop.\n")

        user_query = input("What would you Like to ask ChatGPT? ").strip()

        if not user_query or user_query.lower() == 'exit':
            print("[*] Deactivating active session connection loop. Goodbye.")
            return

        print("\n[*] Packing token structures and dispatching request to GitHub Models...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",   
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional logistics and geographical data synthesis assistant."
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.8,
        )

        ai_reply = response.choices[0].message.content
        token_metrics = response.usage.total_tokens

        print("\n" + "=" * 65)
        print("                       GITHUB MODELS SYSTEM RESPONSE              ")
        print("=" * 65)
        print(ai_reply)
        print("=" * 65)
        print(f"[*] Audit Logs: Operational Ingestion Complete -> Tokens Consumed: {token_metrics}")
        print("[PASS] Dynamic GitHub Models workflow verified successfully.\n")

    except RateLimitError as rate_err:
        print("\n[FAIL] Rate limit reached for GitHub Models free tier: 429", file=sys.stderr)
    except AuthenticationError:
        print("\n[FAIL] Security Clearance Exception: GitHub token rejected.", file=sys.stderr)
    except APIConnectionError:
        print("\n[FAIL] Network Failure: Infrastructure unreachable.", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n\n[WAKE HALT] Loop interrupted. Closing session cleanly.")
    except Exception as err:
        print(f"\n[FAIL] System Error: Unexpected pipeline break: {err}", file=sys.stderr)

if __name__ == "__main__":
    execute_dynamic_cloud_assistant()
