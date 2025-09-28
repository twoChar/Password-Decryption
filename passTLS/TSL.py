import torch
from tqdm import tqdm
import torch.nn as nn
import torch.optim as optim
import math
from MHSA import PassTSL


# save as pass_tsl_toy.py and run in a Python environment with PyTorch installed
import string
import math
import random
from typing import List

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# -----------------------
# 1) Vocabulary / Tokenizer
# -----------------------
# 95 printable ASCII characters (space..~) as in paper; we'll also add specials
PRINTABLE = ''.join([chr(i) for i in range(32, 127)])  # len 95

SPECIAL_TOKENS = ["[PAD]", "[SOS]", "[EOS]", "[UNK]", "[MASK]"]
ALL_TOKENS = SPECIAL_TOKENS + list(PRINTABLE)
VOCAB_SIZE = len(ALL_TOKENS)

stoi = {s: i for i, s in enumerate(ALL_TOKENS)}
itos = {i: s for s, i in stoi.items()}

def encode_password(pw: str, max_len: int = None) -> List[int]:
    """Encode a password string to token ids (no SOS/EOS here)."""
    ids = []
    for ch in pw:
        if ch in PRINTABLE:
            ids.append(stoi[ch])
        else:
            ids.append(stoi["[UNK]"])
    if max_len is not None:
        ids = ids[:max_len]
    return ids

def decode_ids(ids: List[int]) -> str:
    return ''.join(itos[i] for i in ids if itos[i] not in SPECIAL_TOKENS)

# -----------------------
# 2) Dataset
# -----------------------
class PasswordDataset(Dataset):
    def __init__(self, passwords: List[str], max_seq_len: int = 64):
        self.passwords = passwords
        self.max_seq_len = max_seq_len

    def __len__(self):
        return len(self.passwords)

    def __getitem__(self, idx):
        pw = self.passwords[idx]
        ids = encode_password(pw, max_len=self.max_seq_len-2)  # leave space for SOS/EOS
        return torch.tensor(ids, dtype=torch.long)

# -----------------------
# 3) Collate (pad + add SOS/EOS)
# -----------------------
PAD_ID = stoi["[PAD]"]
SOS_ID = stoi["[SOS]"]
EOS_ID = stoi["[EOS]"]

def collate_fn(batch):
    """
    batch: list of LongTensors (raw encoded chars)
    returns: input_ids (B, T), target_ids (B, T)
    where inputs start with SOS and targets are inputs shifted left (next-token)
    """
    B = len(batch)
    lengths = [b.size(0) for b in batch]
    max_len = max(lengths) + 2  # +SOS +EOS

    input_ids = torch.full((B, max_len), PAD_ID, dtype=torch.long)
    target_ids = torch.full((B, max_len), PAD_ID, dtype=torch.long)

    for i, b in enumerate(batch):
        L = b.size(0)
        # inputs: [SOS] + b + [EOS] + PAD...
        input_ids[i, 0] = SOS_ID
        input_ids[i, 1:1+L] = b
        input_ids[i, 1+L] = EOS_ID

        # targets: b + [EOS] (model should predict char1..EOS given inputs)
        target_ids[i, :L+1] = torch.cat([b, torch.tensor([EOS_ID])])

    return input_ids, target_ids  # shapes (B, T), (B, T)


def train_model(model, data_loader, num_epochs=10, learning_rate=0.001, device='mps'):
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    model.train()
    for epoch in tqdm(range(num_epochs)):
        total_loss = 0
        for inputs, targets in data_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs.view(-1, outputs.size(-1)), targets.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(data_loader)}")



if __name__ == "__main__":
    # read the rock-you list
    with open("rockyou.txt", "r", encoding="latin-1") as f:
        passwords = [line.strip() for line in f if 0 < len(line.strip()) <= 30]
    dataset = PasswordDataset(passwords[:10000], max_seq_len=32)
    loader = DataLoader(dataset, batch_size=1000, shuffle=True, collate_fn=collate_fn, num_workers=6)
    print("data loader ready...")
    model = PassTSL(vocab_size=VOCAB_SIZE, d_model=128, num_heads=4, d_ff=512, num_layers=4, max_len=64, dropout=0.1)
    train_model(model, loader, num_epochs=5, learning_rate=0.001, device='mps')
    # save the model
    torch.save(model.state_dict(), "pass_tsl_model.pth")

