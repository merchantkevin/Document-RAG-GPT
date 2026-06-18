"""Split text into overlapping chunks, respecting paragraph boundaries."""
from typing import List


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # 1) Greedily pack paragraphs into blocks up to chunk_size.
    blocks: List[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if current:
                blocks.append(current)
                current = ""
            # hard-split an oversized paragraph with a sliding window
            step = max(1, chunk_size - overlap)
            for start in range(0, len(para), step):
                blocks.append(para[start:start + chunk_size])
        elif len(current) + len(para) + 1 <= chunk_size:
            current = f"{current}\n{para}".strip()
        else:
            blocks.append(current)
            current = para
    if current:
        blocks.append(current)

    # 2) Add overlap by prepending the tail of the previous block.
    if overlap <= 0 or len(blocks) <= 1:
        return blocks
    out = [blocks[0]]
    for i in range(1, len(blocks)):
        tail = blocks[i - 1][-overlap:]
        out.append(f"{tail}\n{blocks[i]}".strip())
    return out
