import os
import json
from voice_pipeline import VoicePipeline

# Pipeline initialize karein
pipeline = VoicePipeline()

# Test Scenarios ki Audios List
test_cases = [
    # Male / Female / Different Scenarios
    {"file": "test_audios/test_location.mp3", "scenario": "Standard Available with Location"},
    {"file": "test_audios/test_busy_time.mp3", "scenario": "Busy with Time Duration"},
    {"file": "test_audios/test_ambiguous.mp3", "scenario": "Unclear / Ambiguous Intent"},
    {"file": "test_audios/test_incomplete.mp3", "scenario": "Incomplete Sentence"},
    {"file": "test_audios/test_mixed.mp3", "scenario": "Mixed Intent (Busy then Available)"},
    # Aap mazeed audios yahan add kar sakti hain (Total 10-12)
]

results_summary = []

print("=== STARTING BATCH TESTING ===\n")

for test in test_cases:
    audio_path = test["file"]
    scenario = test["scenario"]
    
    if not os.path.exists(audio_path):
        print(f"Skipping {audio_path}: File not found.")
        continue

    print(f"Testing Scenario: {scenario} ({audio_path})...")
    res = pipeline.process_voice_command(audio_path)
    
    # Check if passed or failed
    status = "PASS" if "error" not in res and res.get("intent") else "FAIL"
    
    results_summary.append({
        "scenario": scenario,
        "file": audio_path,
        "transcript": res.get("transcript", "N/A"),
        "intent": res.get("intent", "N/A"),
        "area": res.get("area", "N/A"),
        "duration": res.get("duration", "N/A"),
        "status": status
    })

print("\n=== FINAL TEST REPORT ===")
print(json.dumps(results_summary, ensure_ascii=False, indent=2))