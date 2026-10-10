import json
from pathlib import Path

path = Path("data/articles/PMC10025752.json")

with path.open("r", encoding="utf-8") as file:
    article = json.load(file)

introduction = next(
    (
        section["text"]
        for section in article["sections"]
        if section.get("heading", "").lower() == "introduction"
    ),
    None,
)

if introduction is None:
    raise ValueError("Introduction section not found.")

print("INTRODUCTION EXCERPT")
print(introduction[:1800])

print("\nMISSING-SPACE CHECKS")
print(
    'Contains "such asmatrix":',
    "such asmatrix" in introduction,
)
print(
    'Contains "andsequencing":',
    "andsequencing" in introduction,
)