import random

# Simple PCFG rules
grammar = {
    "S": [("W D", 1.0)],   # Start → Word + Digit
    "W": [("hello", 0.3), ("love", 0.4), ("dragon", 0.3)],
    "D": [("123", 0.5), ("2024", 0.5)]
}

def generate(symbol="S"):
    if symbol not in grammar:  # Terminal case
        return symbol
    rules = grammar[symbol]
    parts, probs = zip(*rules)
    choice = random.choices(parts, weights=probs)[0]
    return " ".join(generate(p) for p in choice.split())

# Generate passwords
for _ in range(5):
    print(generate().replace(" ", ""))
