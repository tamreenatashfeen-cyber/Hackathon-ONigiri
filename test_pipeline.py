from main import process_voice_intent

test_files = ["test_voice_1_ali.mp3", "test_voice_2_ayan.mp3", "test_voice_3_mine.mp3"]

print("=== Starting Voice AI Pipeline Test ===\n")

for file_name in test_files:
    print(f"Testing File: {file_name}")
    result = process_voice_intent(file_name)
    print("Result:", result)
    print("-" * 50)