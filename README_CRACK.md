# Password Cracking Tool for Mock2 Files

This tool attempts to crack password-protected Office documents (DOCX, PPTX, XLSX) and PDF files using a wordlist.

## Files

- `crack_mock2.py` - Main cracking script
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

- Wordlist size: 15,018 passwords
- Target files: 25 files
- Total combinations: 375,450
- Expected time: Varies depending on system (typically 5-30 minutes)

## Example Output

```
======================================================================
Password Cracking Tool - Mock2 Files
======================================================================
[*] Loading passwords from: indian-wordlist/all-indian.txt
[+] Loaded 15018 passwords
[*] Scanning target directory: Files/Mock2
[+] Found 15 Office files and 10 PDF files

[*] Cracking: Gc_PS7_Mock2_test1.docx
[*] Testing 15018 passwords...
[+] SUCCESS! Password found for Gc_PS7_Mock2_test1.docx
    Password: 123456
    Attempts: 212
    Time: 3.45 seconds
```

## Notes

- This is a defensive security tool for educational purposes
- Only use on files you have permission to access
- The script attempts passwords in order from the wordlist
- Some files may not be crackable if the password is not in the wordlist
