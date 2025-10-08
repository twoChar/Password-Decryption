#!/bin/bash
# Setup script for password cracking dependencies

echo "========================================="
echo "Installing dependencies for crack_mock2.py"
echo "========================================="

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 not found. Please install python3-pip first:"
    echo "  sudo apt-get install python3-pip"
    exit 1
fi

# Install required Python packages
echo ""
echo "[*] Installing Python packages..."
pip3 install -r requirements.txt

# Verify installation
echo ""
echo "[*] Verifying installation..."
python3 -c "import msoffcrypto; print('[+] msoffcrypto-tool: OK')" 2>/dev/null || echo "[-] msoffcrypto-tool: FAILED"
python3 -c "import pikepdf; print('[+] pikepdf: OK')" 2>/dev/null || echo "[-] pikepdf: FAILED"

echo ""
echo "========================================="
echo "Setup complete! Run the script with:"
echo "  python3 crack_mock2.py"
echo "========================================="
