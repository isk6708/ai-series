
#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Module 2: Local AI API & Ingestion Handling Verification
Component: Dynamic Terminal User Input Interface

Features:
- Local Ollama API integration
- Llama 3.2 language model
- Continuous terminal interaction
- Dynamic user input
- Exit command handling
"""

import sys
from openai import OpenAI
from openai import APIConnectionError


def run_dynamic_assistant():

    try:
        # Initialize the client package targeting the local hardware framework bus
        client = OpenAI(
            base_url="http://localhost:11434/v1",  # Local Ollama port endpoint
            api_key="ollama"                       # Placeholder API key
        )

        print("=" * 60)
        print("         DYNAMIC LOCAL AI ASSISTANT RUNTIME ACTIVE          ")
        print("=" * 60)
        print("[*] Engine Status: Llama3.2 pipeline active offline.")
        print("[*] Instructions: Type your question below and press Enter.")
        print("[*] Operations: Type 'exit' to terminate the session.")
        print("[*] You can ask multiple questions during this session.\n")

        # Continuous terminal interaction loop
        while True:

            # Capture dynamic natural language intent from the terminal
            user_query = input("\nWhat would you like to ask the AI? ").strip()

            # Graceful exit handling if user explicitly wants to quit
            if user_query.lower() == 'exit':
                print("\n[*] Deactivating assistant session. Goodbye.")
                break

            # Validate empty input
            if not user_query:
                print("[WARNING] Empty input detected. Please enter a question.")
                continue

            print("\n[*] Processing token payloads through local inference tracks...")

            # Execute the dynamic completion request
            response = client.chat.completions.create(
                model="llama3.2",
                messages=[
                    # {
                    #     "role": "system",
                    #     "content": "You are a professional enterprise database and integration assistant."
                    # },
                    {
                        "role": "user",
                        "content": user_query
                    }
                ],
                temperature=0.8,
            )

            # Safely extract the generated AI response
            ai_reply = response.choices[0].message.content

            print("\n" + "=" * 60)
            print("                      ASSISTANT RESPONSE")
            print("=" * 60)
            print(ai_reply)
            print("=" * 60)
            print("[PASS] Dynamic interaction loop executed successfully.")

    except APIConnectionError:
        print(
            "\n[FAIL] Connection Error: Ollama is not running. "
            "Verify that the Ollama service is active.",
            file=sys.stderr
        )

    except KeyboardInterrupt:
        print("\n\n[WAKE HALT] Execution interrupted by trainer command. Exiting.")

    except Exception as err:
        print(
            f"\n[FAIL] Pipeline Execution Exception: {err}",
            file=sys.stderr
        )


if __name__ == "__main__":
    run_dynamic_assistant()
