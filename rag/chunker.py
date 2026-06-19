"""Split text into chunks. Article-structured documents are split one chunk per
article; other documents fall back to paragraph-aware packing with overlap."""
import re
from typing import List

# Matches an article header at the start of a line, e.g. "Article 21." / "Article 51A".
ARTICLE_RE = re.compile(r"(?m)^[ \t]*Article\s+\d+[A-Z]?\b")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    starts = [m.start() for m in ARTICLE_RE.finditer(text)]
    if starts:
        # Article-structured document: one chunk per article.
        segments: List[str] = []
        if starts[0] > 0:                      # leading material (preamble, titles)
            lead = text[:starts[0]].strip()
            if lead:
                segments.append(lead)
        bounds = starts + [len(text)]
        for i in range(len(starts)):
            seg = text[bounds[i]:bounds[i + 1]].strip()
            if seg:
                segments.append(seg)
        chunks: List[str] = []
        for seg in segments:                   # sub-split only oversized articles
            if len(seg) <= chunk_size:
                chunks.append(seg)
            else:
                chunks.extend(_pack_paragraphs(seg, chunk_size, overlap))
        return chunks

    # Generic fallback for arbitrary uploaded documents.
    return _pack_paragraphs(text, chunk_size, overlap)


def _pack_paragraphs(text: str, chunk_size: int, overlap: int) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    blocks: List[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if current:
                blocks.append(current)
                current = ""
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

    if overlap <= 0 or len(blocks) <= 1:
        return blocks
    out = [blocks[0]]
    for i in range(1, len(blocks)):
        tail = blocks[i - 1][-overlap:]
        out.append(f"{tail}\n{blocks[i]}".strip())
    return out