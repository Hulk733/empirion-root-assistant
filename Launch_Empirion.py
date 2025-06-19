import json
import time

def load_memory():
    try:
        with open("memory.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_memory(memory):
    with open("memory.json", "w") as f:
        json.dump(memory, f)

def main():
    print("Empirion AI Assistant is starting...")
    memory = load_memory()
    if not memory:
        print("No memory found, initializing...")
        memory = {"reminders": [], "preferences": {}}
        save_memory(memory)

    print("Hello! Empirion is ready to assist you.")
    # This is a stub loop for future voice commands
    try:
        while True:
            cmd = input("Say something: ")
            if cmd.lower() in ["exit", "quit", "stop"]:
                print("Goodbye!")
                break
            else:
                print(f"Echo: {cmd}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutting down Empirion.")

if __name__ == "__main__":
    main()
