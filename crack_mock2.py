#!/usr/bin/env python3
"""
Password Cracking Script for Mock2 Files
Attempts to crack password-protected Office documents and PDFs using a wordlist
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import msoffcrypto
except ImportError:
    print("ERROR: msoffcrypto-tool not installed. Install with: pip install msoffcrypto-tool")
    sys.exit(1)

try:
    import pikepdf
except ImportError:
    print("ERROR: pikepdf not installed. Install with: pip install pikepdf")
    sys.exit(1)


class PasswordCracker:
    def __init__(self, wordlist_path, target_dir, min_length=6, max_length=12):
        self.wordlist_path = Path(wordlist_path)
        self.target_dir = Path(target_dir)
        self.min_length = min_length
        self.max_length = max_length
        self.results = []
        self.attempts = 0

    def load_passwords(self):
        """Load passwords from wordlist file and filter by length"""
        print(f"[*] Loading passwords from: {self.wordlist_path}")
        print(f"[*] Filtering passwords: length {self.min_length}-{self.max_length} characters")
        try:
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_passwords = [line.strip() for line in f if line.strip()]

            # Filter by length
            passwords = [p for p in all_passwords if self.min_length <= len(p) <= self.max_length]

            print(f"[+] Loaded {len(all_passwords)} total passwords")
            print(f"[+] Filtered to {len(passwords)} passwords (length {self.min_length}-{self.max_length})")
            print(f"[+] Skipped {len(all_passwords) - len(passwords)} passwords outside length range")
            return passwords
        except Exception as e:
            print(f"[-] Error loading wordlist: {e}")
            sys.exit(1)

    def get_target_files(self):
        """Get all files from target directory"""
        print(f"[*] Scanning target directory: {self.target_dir}")
        files = list(self.target_dir.glob("*"))
        office_files = [f for f in files if f.suffix.lower() in ['.docx', '.pptx', '.xlsx']]
        pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
        print(f"[+] Found {len(office_files)} Office files and {len(pdf_files)} PDF files")
        return office_files, pdf_files

    def try_office_password(self, file_path, password):
        """Try to decrypt an Office file with given password"""
        try:
            with open(file_path, 'rb') as f:
                office_file = msoffcrypto.OfficeFile(f)
                office_file.load_key(password=password)
                # Try to decrypt to verify password
                with open('/dev/null', 'wb') as out:
                    office_file.decrypt(out)
            return True
        except Exception:
            return False

    def try_pdf_password(self, file_path, password):
        """Try to open a PDF file with given password"""
        try:
            with pikepdf.open(file_path, password=password) as pdf:
                return True
        except pikepdf.PasswordError:
            return False
        except Exception:
            return False

    def crack_file(self, file_path, passwords):
        """Attempt to crack a single file"""
        file_name = file_path.name
        file_ext = file_path.suffix.lower()

        print(f"\n[*] Cracking: {file_name}")
        print(f"[*] Testing {len(passwords)} passwords...")

        start_time = datetime.now()

        for idx, password in enumerate(passwords, 1):
            self.attempts += 1

            # Progress indicator every 1000 attempts
            if idx % 1000 == 0:
                print(f"    Progress: {idx}/{len(passwords)} passwords tested...", end='\r')

            # Try the appropriate method based on file type
            success = False
            if file_ext in ['.docx', '.pptx', '.xlsx']:
                success = self.try_office_password(file_path, password)
            elif file_ext == '.pdf':
                success = self.try_pdf_password(file_path, password)

            if success:
                elapsed = (datetime.now() - start_time).total_seconds()
                result = {
                    'file': file_name,
                    'password': password,
                    'attempts': idx,
                    'time': elapsed
                }
                self.results.append(result)
                print(f"\n[+] SUCCESS! Password found for {file_name}")
                print(f"    Password: {password}")
                print(f"    Attempts: {idx}")
                print(f"    Time: {elapsed:.2f} seconds")
                return True

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n[-] Failed to crack {file_name} after {len(passwords)} attempts ({elapsed:.2f}s)")
        return False

    def run(self):
        """Main execution method"""
        print("="*70)
        print("Password Cracking Tool - Mock2 Files")
        print("="*70)

        # Load passwords
        passwords = self.load_passwords()

        # Get target files
        office_files, pdf_files = self.get_target_files()
        all_files = office_files + pdf_files

        if not all_files:
            print("[-] No files found to crack!")
            return

        print(f"\n[*] Starting crack attempt on {len(all_files)} files...")
        print(f"[*] Total combinations: {len(passwords)} passwords × {len(all_files)} files = {len(passwords) * len(all_files)}")

        start_time = datetime.now()

        # Try to crack each file
        for file_path in all_files:
            self.crack_file(file_path, passwords)

        # Summary
        total_time = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total files tested: {len(all_files)}")
        print(f"Successfully cracked: {len(self.results)}")
        print(f"Failed to crack: {len(all_files) - len(self.results)}")
        print(f"Total attempts: {self.attempts}")
        print(f"Total time: {total_time:.2f} seconds")

        if self.results:
            print("\n" + "="*70)
            print("CRACKED FILES")
            print("="*70)
            for result in self.results:
                print(f"\nFile: {result['file']}")
                print(f"  Password: {result['password']}")
                print(f"  Attempts: {result['attempts']}")
                print(f"  Time: {result['time']:.2f}s")

            # Save results to file
            output_file = Path(__file__).parent / 'cracked_passwords.txt'
            with open(output_file, 'w') as f:
                f.write("Cracked Passwords - Mock2 Files\n")
                f.write("="*70 + "\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for result in self.results:
                    f.write(f"File: {result['file']}\n")
                    f.write(f"Password: {result['password']}\n")
                    f.write(f"Attempts: {result['attempts']}\n")
                    f.write(f"Time: {result['time']:.2f}s\n\n")
            print(f"\n[+] Results saved to: {output_file}")

        print("="*70)


if __name__ == "__main__":
    # Paths
    WORDLIST = "/home/tu-mbg/Documents/cc-show-around/PD/Password-Decryption/indian-wordlist/all-indian.txt"
    TARGET_DIR = "/home/tu-mbg/Documents/cc-show-around/PD/Password-Decryption/Files/Mock2"

    # Check if paths exist
    if not Path(WORDLIST).exists():
        print(f"[-] Wordlist not found: {WORDLIST}")
        sys.exit(1)

    if not Path(TARGET_DIR).exists():
        print(f"[-] Target directory not found: {TARGET_DIR}")
        sys.exit(1)

    # Run cracker
    cracker = PasswordCracker(WORDLIST, TARGET_DIR)
    cracker.run()
