"""Run: python test_claude_client.py — tests Claude API connection and memory."""
import sys
import config

errors = config.validate()
if errors:
    print("Config errors:", errors)
    sys.exit(1)

print(f"Sending test message to {config.CLAUDE_MODEL}...")
import claude_client

response = claude_client.ask("Say hello and confirm you are working as a voice assistant.")
print(f"\nClaude: {response}")

print("\nSending follow-up (tests conversation memory)...")
response2 = claude_client.ask("What did I just ask you?")
print(f"Claude: {response2}")

print("\nClaude client test complete.")
