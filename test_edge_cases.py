from main import process_voice_intent

test_files = [
    "test_mixed.mp3",
    "test_ambiguous.mp3",
    "test_incomplete.mp3"
]

print("=== Edge Cases Testing Start ===\n")

for file in test_files:
    print(f"Testing File: {file}")
    try:
        result = process_voice_intent(file)
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Error processing {file}: {e}\n")

print("=== Edge Cases Testing Complete ===")