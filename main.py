import random
import msoffcrypto
import io

# Simple PCFG grammar
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
    return "".join(generate(p) for p in choice.split())

# Path to the password-protected file
file_path = "Mock/Gc_PS7_Mock_test1.docx"

# Try 5 passwords
for _ in range(5):
    guessed_password = generate()
    # print(f"Trying password: {guessed_password}")

    try:
        with open(file_path, "rb") as f:
            office_file = msoffcrypto.OfficeFile(f)
            office_file.load_key(password=guessed_password)

            decrypted = io.BytesIO()
            office_file.decrypt(decrypted)

            # If no exception, password is correct
            print(f"Success! Password is: {guessed_password}")
            break
    except Exception as e:
        print(f"Failed with password: {guessed_password}")
