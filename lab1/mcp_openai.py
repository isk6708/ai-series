#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Module 2: AI APIs & JSON Handling
Lab: Dynamic Terminal User Interaction Loops targeting OpenAI Cloud Endpoints
"""

import os
import sys
from openai import OpenAI
from openai import RateLimitError, APIConnectionError, AuthenticationError
from dotenv import load_dotenv

# Silently read infrastructure secrets out of local disk storage into system memory
load_dotenv()

def execute_dynamic_cloud_assistant():
    # Retrieve security credentials securely from system environment runtime variables
    api_key_env = os.getenv("AI_PROVIDER_API_KEY")
    
    # Intercept runtime execution if environment config arrays are unallocated
    if not api_key_env or api_key_env.startswith("sk-proj-InsertYourActual"):
        print("\n[FAIL] Configuration Exception: Valid 'AI_PROVIDER_API_KEY' missing from your local .env file.", file=sys.stderr)
        print("       Instruct the student to populate their token string values to pass perimeter security.", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize the official cloud platform client interface gateway
        client = OpenAI(api_key=api_key_env)

        print("=" * 65)
        print("          OPENAI CLOUD INTEGRATION ACTIVE [DYNAMIC INTERFACE]      ")
        print("=" * 65)
        print("[*] Target Deployment Endpoint: https://openai.com")
        print("[*] Target Computational Engine: gpt-4o-mini")
        print("[*] Instructions: Type your question below and press Enter.")
        print("[*] Operations: Type 'exit' to terminate the current execution loop.\n")

        # Capture unstructured conversational request inputs dynamically from the terminal window
        user_query = input("What would you Like to ask ChatGPT? ").strip()

        # Graceful validation check to avoid passing blank payloads across the network perimeter
        if not user_query or user_query.lower() == 'exit':
            print("[*] Deactivating active session connection loop. Goodbye.")
            return

        print("\n[*] Packing token structures and dispatching secure HTTP POST payload payload...")

        # Fire synchronous execution loops matching core Chapter 1 parameters
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

        # Parse the structured JSON response dictionary path down to the text reply choice array
        ai_reply = response.choices[0].message.content
        token_metrics = response.usage.total_tokens

        print("\n" + "=" * 65)
        print("                        CHATGPT SYSTEM RESPONSE                   ")
        print("=" * 65)
        print(ai_reply)
        print("=" * 65)
        print(f"[*] Audit Logs: Operational Ingestion Complete -> Tokens Consumed: {token_metrics}")
        print("[PASS] Dynamic production cloud workflow verified successfully.\n")

    except RateLimitError as rate_err:
        print("\n" + "!" * 65)
        print("               GATEWAY BOUNDARY HALT: FINANCIAL RISK CLASH        ")
        print("!" * 65)
        print(f"[FAIL] Server Error Code: 429 - Wallet depletion event detected.")
        print("       The API token used possesses zero active pre-funded credits.")
        print("       Add funds via: https://platform.openai.com/settings/organization/billing/")
        print("!" * 65, file=sys.stderr)
    except AuthenticationError:
        print("\n[FAIL] Security Clearance Exception: Key rejected by remote validation gates. Verify string integrity.", file=sys.stderr)
    except APIConnectionError:
        print("\n[FAIL] Network Failure: Infrastructure unreachable. Check internet routers.", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n\n[WAKE HALT] Loop interrupted by instructor cancel command. Closing session cleanly.")
    except Exception as err:
        print(f"\n[FAIL] System Error: Unexpected pipeline break: {err}", file=sys.stderr)

if __name__ == "__main__":
    execute_dynamic_cloud_assistant()
