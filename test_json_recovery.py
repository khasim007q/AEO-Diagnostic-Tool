"""Test JSON recovery with truncated/malformed JSON."""
from llm_engine import _try_parse_json

# Test 1: Exact Gemini output from the screenshot (truncated)
truncated = '[{ "rank": 1, "brand": "OnePlus 12R" },'
result = _try_parse_json(truncated)
print("Test 1 - Truncated JSON:", result)
assert result is not None, "Failed to recover from truncated JSON!"
assert result[0] == (1, "OnePlus 12R")
print("  [OK] Recovered brand from truncated JSON")

# Test 2: Multiple brands, truncated mid-object
truncated2 = '[{"rank": 1, "brand": "Xiaomi 14"}, {"rank": 2, "brand": "Samsung Galaxy S24"}, {"rank": 3, "brand":'
result2 = _try_parse_json(truncated2)
print("\nTest 2 - Mid-object truncation:", result2)
assert result2 is not None and len(result2) >= 2
print(f"  [OK] Recovered {len(result2)} brands from mid-object truncation")

# Test 3: Valid JSON still works
valid = '[{"rank": 1, "brand": "iPhone 15"}, {"rank": 2, "brand": "Samsung Galaxy S24"}]'
result3 = _try_parse_json(valid)
print("\nTest 3 - Valid JSON:", result3)
assert len(result3) == 2
print("  [OK] Valid JSON still works")

# Test 4: JSON with preamble text
preamble = 'Here are the top phones:\n[{"rank": 1, "brand": "iPhone 15"}, {"rank": 2, "brand": "Pixel 8"}]'
result4 = _try_parse_json(preamble)
print("\nTest 4 - JSON with preamble:", result4)
assert len(result4) == 2
print("  [OK] Preamble text handled")

print("\n=== ALL JSON RECOVERY TESTS PASSED ===")
