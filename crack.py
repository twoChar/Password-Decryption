# --- FAST PasswordCracker replacement (drop-in) ---
import os
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# Optional progress bar; fallback if tqdm not installed
try:
    from tqdm import tqdm
except Exception:
    def tqdm(iterable=None, **kwargs):
        # simple fallback that only returns the iterable and ignores updates
        class Dummy:
            def __init__(self, it):
                self.it = it
            def update(self, _): pass
            def close(self): pass
        return Dummy(iterable)


# Worker function MUST be top-level so it is picklable for ProcessPoolExecutor
def _try_passwords_worker(file_bytes, suffix, password_slice):
    """
    Worker executed in a separate process.
    Tries every password from password_slice against the provided file_bytes.
    Returns a tuple: (found_password_or_None, attempts_tried)
    """
    attempts = 0
    # local imports inside worker to avoid cross-process import issues
    try:
        import msoffcrypto
    except Exception:
        msoffcrypto = None
    try:
        import pikepdf
    except Exception:
        pikepdf = None

    from io import BytesIO

    for p in password_slice:
        attempts += 1
        try:
            if suffix in ('.docx', '.pptx', '.xlsx'):
                # If msoffcrypto not present, just skip (should not happen if installed)
                if msoffcrypto is None:
                    continue
                bio = BytesIO(file_bytes)
                office_file = msoffcrypto.OfficeFile(bio)
                office_file.load_key(password=p)
                out = BytesIO()
                office_file.decrypt(out)  # raises on failure
                return (p, attempts)
            elif suffix == '.pdf':
                if pikepdf is None:
                    continue
                bio = BytesIO(file_bytes)
                # pikepdf.open raises pikepdf.PasswordError on wrong password
                with pikepdf.open(bio, password=p):
                    return (p, attempts)
            else:
                # unsupported type
                return (None, attempts)
        except Exception:
            # wrong password or other error -> continue
            continue

    return (None, attempts)


class PasswordCracker:
    def __init__(self, wordlist_path, target_dir, min_length=6, max_length=12):
        self.wordlist_path = Path(wordlist_path)
        self.target_dir = Path(target_dir)
        self.min_length = min_length
        self.max_length = max_length
        self.results = []
        self.attempts = 0
        self.current_file = None
        self.current_progress = 0

    def load_passwords(self):
        """Load passwords from wordlist file and filter by length"""
        print(f"📂 Loading passwords from: {self.wordlist_path.name}")
        print(f"🔍 Filtering passwords: length {self.min_length}-{self.max_length} characters")
        try:
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_passwords = [line.strip() for line in f if line.strip()]

            # Filter by length
            passwords = [p for p in all_passwords if self.min_length <= len(p) <= self.max_length]

            print(f"✓ Loaded {len(all_passwords):,} total passwords")
            print(f"✓ Filtered to {len(passwords):,} passwords (length {self.min_length}-{self.max_length})")
            print(f"⏩ Skipped {len(all_passwords) - len(passwords):,} passwords outside length range")
            return passwords
        except Exception as e:
            print(f"✗ Error loading wordlist: {e}")
            return []

    def get_target_files(self):
        """Get all Office/PDF files from target directory"""
        print(f"\n📁 Scanning target directory: {self.target_dir.name}")
        files = list(self.target_dir.glob("*"))
        office_files = [f for f in files if f.suffix.lower() in ['.docx', '.pptx', '.xlsx']]
        pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
        print(f"✓ Found {len(office_files)} Office files and {len(pdf_files)} PDF files")
        return office_files, pdf_files

    def crack_file_fast(self, file_path, passwords, max_workers=None, chunk_size=4096, show_progress=True):
        """
        Fast cracker for a single file:
        - reads file once into memory,
        - splits wordlist into chunks,
        - processes chunks in parallel (ProcessPoolExecutor),
        - cancels remaining tasks on success.
        Returns (found_password_or_None, attempts_total, elapsed_seconds)
        """
        start = time.time()
        suffix = file_path.suffix.lower()
        file_bytes = file_path.read_bytes()  # read once

        n = len(passwords)
        if n == 0:
            return (None, 0, 0.0)

        # Build chunks: list of password slices
        chunks = [passwords[i:i+chunk_size] for i in range(0, n, chunk_size)]

        total_attempts = 0
        found = None

        # If max_workers is None, ProcessPoolExecutor uses os.cpu_count()
        with ProcessPoolExecutor(max_workers=max_workers) as exe:
            futures = {exe.submit(_try_passwords_worker, file_bytes, suffix, chunk): idx for idx, chunk in enumerate(chunks)}
            pbar = tqdm(total=n, desc=f"Cracking {file_path.name}", disable=not show_progress)
            try:
                for fut in as_completed(futures):
                    try:
                        pw, attempts = fut.result()
                    except Exception:
                        # if worker crashed, count its chunk size as attempted
                        attempts = len(chunks[futures[fut]])
                        pw = None

                    total_attempts += attempts
                    try:
                        pbar.update(attempts)
                    except Exception:
                        pass

                    if pw:
                        found = pw
                        # cancel remaining futures
                        for other in futures:
                            if not other.done():
                                other.cancel()
                        break
                pbar.close()
            finally:
                # context manager ensures executor shutdown
                pass

        elapsed = time.time() - start
        return (found, total_attempts, elapsed)

    def run(self, max_workers=None, chunk_size=4096, show_progress=True):
        """Main execution method (uses crack_file_fast for speed)"""
        print("="*70)
        print("🔓 Password Cracking Tool - Mock2 Files (FAST MODE)")
        print("="*70)

        passwords = self.load_passwords()
        if not passwords:
            print("❌ No passwords loaded!")
            return

        office_files, pdf_files = self.get_target_files()
        all_files = office_files + pdf_files
        if not all_files:
            print("❌ No files found to crack!")
            return

        print(f"\n🚀 Starting crack attempt on {len(all_files)} files...")
        print(f"📊 Total combinations: {len(passwords):,} passwords × {len(all_files)} files = {len(passwords) * len(all_files):,}")

        overall_start = time.time()

        for file_path in all_files:
            self.current_file = file_path.name
            print(f"\n🔐 Cracking: {file_path.name}")
            found, attempts, elapsed = self.crack_file_fast(
                file_path,
                passwords,
                max_workers=max_workers,
                chunk_size=chunk_size,
                show_progress=show_progress
            )
            self.attempts += attempts
            if found:
                print(f"\n✅ SUCCESS! Password found for {file_path.name}")
                print(f"   🔑 Password: {found}")
                print(f"   🎯 Attempts: {attempts:,}")
                print(f"   ⏱️  Time: {elapsed:.2f} seconds")
                self.results.append({
                    'file': file_path.name,
                    'password': found,
                    'attempts': attempts,
                    'time': elapsed
                })
            else:
                print(f"\n❌ Failed to crack {file_path.name} after {attempts:,} attempts ({elapsed:.2f}s)")

        total_time = time.time() - overall_start
        print("\n" + "="*70)
        print("📋 SUMMARY")
        print("="*70)
        print(f"Total files tested: {len(all_files)}")
        print(f"✅ Successfully cracked: {len(self.results)}")
        print(f"❌ Failed to crack: {len(all_files) - len(self.results)}")
        print(f"🔢 Total attempts: {self.attempts:,}")
        print(f"⏱️  Total time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")

        if self.results:
            print("\n" + "="*70)
            print("🎉 CRACKED FILES")
            print("="*70)
            for i, result in enumerate(self.results, 1):
                print(f"\n{i}. File: {result['file']}")
                print(f"   🔑 Password: {result['password']}")
                print(f"   🎯 Attempts: {result['attempts']:,}")
                print(f"   ⏱️  Time: {result['time']:.2f}s")

            # Save results
            output_file = Path.cwd() / 'cracked_passwords.txt'
            with open(output_file, 'w') as f:
                f.write("Cracked Passwords - Mock2 Files\n")
                f.write("="*70 + "\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for result in self.results:
                    f.write(f"File: {result['file']}\n")
                    f.write(f"Password: {result['password']}\n")
                    f.write(f"Attempts: {result['attempts']:,}\n")
                    f.write(f"Time: {result['time']:.2f}s\n\n")
            print(f"\n💾 Results saved to: {output_file}")
        else:
            print("\n⚠️  No files were cracked. The passwords may not be in the wordlist.")

        print("="*70)

# --- End replacement ---
if __name__ == "__main__":
    cracker = PasswordCracker(WORDLIST, TARGET_DIR, min_length=6, max_length=12)
    cracker.run(max_workers=None, chunk_size=4000, show_progress=True)


