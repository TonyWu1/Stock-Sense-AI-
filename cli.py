"""Run with: python cli.py"""
import os
from dotenv import load_dotenv
from agent import StockSenseAgent


def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_api_key_here":
        print("Set OPENAI_API_KEY in your .env file first. No charge has been made.")
        return
    agent = StockSenseAgent()
    print("StockSense AI | Text demo | Local simulated inventory | NOT real Alexa+")
    print("Try: 'Which products are low on stock?'")
    print("Try: 'Prepare a restock order under $150.'")
    print("Then type CONFIRM ORDER <number> to approve locally, or 'no' to decline.")
    print("Commands: /reset to clear session, /exit to quit.\n")
    while True:
        try:
            user_text = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
        if user_text.lower() in {"/exit", "/quit"}:
            return
        if user_text.lower() == "/reset":
            agent.reset()
            print("Session reset; saved SQLite orders were not deleted.\n")
            continue
        if user_text:
            print(f"StockSense > {agent.chat(user_text)}\n")


if __name__ == "__main__":
    main()
