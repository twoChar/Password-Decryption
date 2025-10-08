# Password Cracking Tool for Mock2 Files

This tool attempts to crack password-protected Office documents (DOCX, PPTX, XLSX) and PDF files using a wordlist.

## Password Requirements

Based on the target files:
- **Length**: 6 to 12 characters
- **Characters**: Alphanumeric + Symbols
- **Patterns**: Human-like (names, dates, places)

The script automatically filters passwords to match these criteria.

## Files

- `crack_mock2.py` - Main cracking script (Python)
- `crack_mock2.ipynb` - Interactive Jupyter notebook version
- `setup.sh` - Installation script for dependencies
- `requirements.txt` - Python package requirements
- `indian-wordlist/all-indian.txt` - Password wordlist (15,018 passwords)
- `Files/Mock2/` - Directory containing 25 password-protected files

## Setup

1. Install dependencies:
   ```bash
   ./setup.sh
   ```

   Or manually:
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage

Run the cracking script:
```bash
python3 crack_mock2.py
```

The script will:
1. Load all passwords from `indian-wordlist/all-indian.txt`
2. Test each password against all 25 files in `Files/Mock2/`
3. Display progress and results in real-time
4. Save successful cracks to `cracked_passwords.txt`

## Output

The script provides:
- Real-time progress updates (every 1000 passwords)
- Immediate notification when a password is found
- Final summary with:
  - Number of files cracked
  - Total attempts made
  - Time elapsed
- Results saved to `cracked_passwords.txt`

## File Types Supported

- **Office Documents**: .docx, .pptx, .xlsx (using msoffcrypto-tool)
- **PDF Files**: .pdf (using pikepdf)

## Performance

- Wordlist size: 15,018 total passwords
- Filtered passwords: 13,784 (length 6-12 chars)
- Skipped passwords: 1,234 (outside length range)
- Target files: 25 files
- Total combinations: 344,600 (13,784 × 25)
- Expected time: Varies depending on system (typically 5-20 minutes)

## Example Output

```
======================================================================
Password Cracking Tool - Mock2 Files
======================================================================
[*] Loading passwords from: indian-wordlist/all-indian.txt
[*] Filtering passwords: length 6-12 characters
[+] Loaded 15018 total passwords
[+] Filtered to 13784 passwords (length 6-12)
[+] Skipped 1234 passwords outside length range
[*] Scanning target directory: Files/Mock2
[+] Found 15 Office files and 10 PDF files

[*] Cracking: Gc_PS7_Mock2_test1.docx
[*] Testing 13784 passwords...
[+] SUCCESS! Password found for Gc_PS7_Mock2_test1.docx
    Password: password123
    Attempts: 347
    Time: 5.21 seconds
```

## Notes

- This is a defensive security tool for educational purposes
- Only use on files you have permission to access
- The script attempts passwords in order from the wordlist
- Some files may not be crackable if the password is not in the wordlist
