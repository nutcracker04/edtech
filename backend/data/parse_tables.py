import json

def explore_json():
    with open("output/20260220_7eddb625-c155-4f11-9acd-aa193f4ef8d7/metadata/page_160.json") as f:
        data = json.load(f)
        for block in data:
            if block.get("layout_tag") == "image":
                print("Found image block:", block)
            elif block.get("layout_tag") == "table":
                print("Found table block:", block)
explore_json()
