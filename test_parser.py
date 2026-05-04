"""Quick smoke test for the new parser + LLM engine pipeline."""
from llm_engine import _try_parse_json
from parser import parse_llm_response, extract_brands, fuzzy_match_brand, fuzzy_find_in_text

# ─── Test 1: JSON parsing ─────────────────────────────────────────────────────
print("=== Test 1: JSON Parsing ===")
json_text = '[{"rank": 1, "brand": "Optimum Nutrition Gold Standard 100% Whey"}, {"rank": 2, "brand": "BSN SYNTHA-6 Edge"}, {"rank": 3, "brand": "MyProtein Impact Whey Protein"}, {"rank": 4, "brand": "Dymatize ISO100"}, {"rank": 5, "brand": "MuscleTech Nitro-Tech"}]'
result = _try_parse_json(json_text)
print(f"  Parsed {len(result)} brands:")
for rank, brand in result:
    print(f"    {rank}. {brand}")
assert len(result) == 5
assert result[0] == (1, "Optimum Nutrition Gold Standard 100% Whey")
print("  [OK] JSON parsing preserves % and full names")

# ─── Test 2: JSON with code fences ────────────────────────────────────────────
print("\n=== Test 2: JSON with code fences ===")
fenced = "```json\n" + json_text + "\n```"
result2 = _try_parse_json(fenced)
assert result2 is not None and len(result2) == 5
print("  [OK] Code-fenced JSON handled correctly")

# ─── Test 3: Regex fallback ──────────────────────────────────────────────────
print("\n=== Test 3: Regex Fallback ===")
text = """Here are the top 5 whey proteins:
1. Optimum Nutrition Gold Standard 100% Whey - Best overall
2. BSN SYNTHA-6 Edge - Best for taste
3. MyProtein Impact Whey Protein - Best value
4. Dymatize ISO100 Hydrolyzed - Best for digestion
5. MuscleTech Nitro-Tech 100% Whey Gold - Best for muscle"""
result3 = extract_brands(text)
print(f"  Parsed {len(result3)} brands:")
for rank, brand in result3:
    print(f"    {rank}. {brand}")
assert len(result3) == 5
# Check that % is preserved
assert any("100%" in b for _, b in result3), "% was stripped from brand names!"
print("  [OK] Regex fallback preserves % in brand names")

# ─── Test 4: parse_llm_response prefers JSON ────────────────────────────────
print("\n=== Test 4: JSON-first pipeline ===")
json_brands = [(1, "Brand A"), (2, "Brand B")]
result4 = parse_llm_response("some raw text", json_brands=json_brands)
assert result4 == json_brands
print("  [OK] JSON result preferred over raw text")

result5 = parse_llm_response(text, json_brands=None)
assert len(result5) == 5
print("  [OK] Falls back to regex when JSON unavailable")

# ─── Test 5: Fuzzy matching ──────────────────────────────────────────────────
print("\n=== Test 5: Fuzzy Matching ===")
assert fuzzy_match_brand("optimum nutrition", "Optimum Nutrition Gold Standard 100% Whey", threshold=70)
assert not fuzzy_match_brand("completely different", "Optimum Nutrition", threshold=85)
assert fuzzy_match_brand("nature made", "Nature Made Wellblends Calm & Relax", threshold=70)
print("  [OK] Fuzzy brand matching works correctly")

# ─── Test 6: Fuzzy find in text ──────────────────────────────────────────────
print("\n=== Test 6: Fuzzy Find in Text ===")
google_snippet = "The best whey protein powders include Optimum Nutrition's Gold Standard and BSN Syntha-6"
assert fuzzy_find_in_text("Optimum Nutrition Gold Standard", google_snippet)
assert fuzzy_find_in_text("BSN SYNTHA-6", google_snippet)
print("  [OK] Fuzzy text search works in Google snippets")

print("\n=== ALL 6 TESTS PASSED ===")
