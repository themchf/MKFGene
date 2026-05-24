"""
utils/sequence_utils.py
Pure-Python sequence analysis utilities (no biopython required).
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Optional

# ── Constants ─────────────────────────────────────────────────────
IUPAC_DNA = set("ACGTNRYSWKMBDHV")

CODON_TABLE = {
    "TTT":"F","TTC":"F","TTA":"L","TTG":"L",
    "CTT":"L","CTC":"L","CTA":"L","CTG":"L",
    "ATT":"I","ATC":"I","ATA":"I","ATG":"M",
    "GTT":"V","GTC":"V","GTA":"V","GTG":"V",
    "TCT":"S","TCC":"S","TCA":"S","TCG":"S",
    "CCT":"P","CCC":"P","CCA":"P","CCG":"P",
    "ACT":"T","ACC":"T","ACA":"T","ACG":"T",
    "GCT":"A","GCC":"A","GCA":"A","GCG":"A",
    "TAT":"Y","TAC":"Y","TAA":"*","TAG":"*",
    "CAT":"H","CAC":"H","CAA":"Q","CAG":"Q",
    "AAT":"N","AAC":"N","AAA":"K","AAG":"K",
    "GAT":"D","GAC":"D","GAA":"E","GAG":"E",
    "TGT":"C","TGC":"C","TGA":"*","TGG":"W",
    "CGT":"R","CGC":"R","CGA":"R","CGG":"R",
    "AGT":"S","AGC":"S","AGA":"R","AGG":"R",
    "GGT":"G","GGC":"G","GGA":"G","GGG":"G",
}

COMPLEMENT = str.maketrans("ACGTacgt", "TGCAtgca")


# ── Parsing ───────────────────────────────────────────────────────

def parse_fasta(text: str) -> Dict[str, str]:
    """Parse FASTA or raw sequence into {name: sequence} dict."""
    text = text.strip()
    if not text.startswith(">"):
        # Raw sequence
        seq = re.sub(r"\s+", "", text).upper()
        return {"sequence_1": seq} if seq else {}

    records = {}
    current_name = None
    current_seq: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_name is not None:
                records[current_name] = "".join(current_seq).upper()
            current_name = line[1:].split()[0] or f"seq_{len(records)+1}"
            current_seq = []
        else:
            current_seq.append(re.sub(r"\s+", "", line))

    if current_name is not None:
        records[current_name] = "".join(current_seq).upper()

    return records


def detect_sequence_type(seq: str) -> str:
    """Heuristically detect DNA / RNA / Protein."""
    seq_upper = seq.upper().replace(" ", "")
    if not seq_upper:
        return "Unknown"
    counts = Counter(seq_upper)
    total = len(seq_upper)
    dna_chars  = sum(counts.get(c, 0) for c in "ACGTN")
    rna_chars  = sum(counts.get(c, 0) for c in "ACGUN")
    if counts.get("U", 0) > 0 and counts.get("T", 0) == 0:
        return "RNA"
    if dna_chars / total > 0.90:
        return "DNA"
    aa_chars = sum(counts.get(c, 0) for c in "ACDEFGHIKLMNPQRSTVWY")
    if aa_chars / total > 0.75:
        return "Protein"
    return "DNA"


# ── Basic Stats ───────────────────────────────────────────────────

def compute_gc_content(seq: str) -> float:
    seq = seq.upper()
    gc = seq.count("G") + seq.count("C")
    total = sum(seq.count(c) for c in "ACGTU")
    return (gc / total * 100) if total else 0.0


def gc_by_window(seq: str, window: int = 100) -> Tuple[List[int], List[float]]:
    seq = seq.upper()
    positions, values = [], []
    for i in range(0, len(seq) - window + 1, window // 2):
        chunk = seq[i:i + window]
        gc = (chunk.count("G") + chunk.count("C")) / len(chunk) * 100
        positions.append(i + window // 2)
        values.append(round(gc, 2))
    return positions, values


def nucleotide_composition(seq: str, seq_type: str = "DNA") -> Dict[str, float]:
    seq = seq.upper()
    total = len(seq)
    if total == 0:
        return {}
    if seq_type == "Protein":
        chars = sorted(set(seq))
    elif seq_type == "RNA":
        chars = ["A", "U", "G", "C"]
    else:
        chars = ["A", "T", "G", "C"]
    return {c: round(seq.count(c) / total * 100, 2) for c in chars if c in seq}


# ── Sequence Operations ───────────────────────────────────────────

def reverse_complement(seq: str) -> str:
    return seq.upper().translate(COMPLEMENT)[::-1]


def translate_sequence(seq: str, frame: int = 0) -> str:
    seq = seq.upper()[frame:]
    protein = []
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i:i+3]
        aa = CODON_TABLE.get(codon, "?")
        if aa == "*":
            break
        protein.append(aa)
    return "".join(protein)


# ── ORF Detection ─────────────────────────────────────────────────

def find_orfs(seq: str, min_length: int = 100) -> List[Dict]:
    """Find ORFs in all 6 reading frames."""
    seq = seq.upper()
    rc  = reverse_complement(seq)
    orfs = []

    for strand, s in [(1, seq), (-1, rc)]:
        for frame in range(3):
            i = frame
            while i < len(s) - 2:
                codon = s[i:i+3]
                if codon == "ATG":
                    # Find stop
                    j = i + 3
                    while j < len(s) - 2:
                        stop = s[j:j+3]
                        if stop in ("TAA", "TAG", "TGA"):
                            length = j + 3 - i
                            if length >= min_length:
                                start_pos = i if strand == 1 else len(seq) - j - 3
                                end_pos   = j + 3 if strand == 1 else len(seq) - i
                                orfs.append({
                                    "start":    start_pos,
                                    "end":      end_pos,
                                    "frame":    strand * (frame + 1),
                                    "length":   length,
                                    "sequence": s[i:j+3],
                                    "strand":   "+" if strand == 1 else "-",
                                })
                            break
                        j += 3
                    i = j + 3
                else:
                    i += 3

    orfs.sort(key=lambda x: x["length"], reverse=True)
    return orfs


# ── Codon Usage ───────────────────────────────────────────────────

def codon_usage(seq: str) -> Dict[str, int]:
    seq = seq.upper().replace("U", "T")
    counts: Dict[str, int] = {}
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i:i+3]
        if len(codon) == 3 and all(c in "ACGT" for c in codon):
            counts[codon] = counts.get(codon, 0) + 1
    return counts


# ── Motif Search ──────────────────────────────────────────────────

def find_motifs(seq: str, motifs: List[str]) -> Dict[str, List[int]]:
    seq = seq.upper()
    results = {}
    for motif in motifs:
        motif = motif.upper()
        positions = [m.start() for m in re.finditer(f"(?={re.escape(motif)})", seq)]
        results[motif] = positions
    return results


# ── Quick Analyze (dashboard) ─────────────────────────────────────

def quick_analyze(text: str) -> str:
    """Fast synchronous summary — no AI call, pure computation."""
    seqs = parse_fasta(text)
    if not seqs:
        return "<p style='color:var(--accent-warn)'>Could not parse sequence.</p>"

    lines = []
    for name, seq in seqs.items():
        seq_type = detect_sequence_type(seq)
        gc       = compute_gc_content(seq) if seq_type in ("DNA","RNA") else None
        orfs     = find_orfs(seq) if seq_type == "DNA" else []

        lines.append(f"**{name}** · {seq_type} · {len(seq):,} bp")
        if gc is not None:
            lines.append(f"- GC content: **{gc:.1f}%**")
        if orfs:
            lines.append(f"- ORFs detected (≥100 bp): **{len(orfs)}** · Longest: **{orfs[0]['length']} bp**")
        if seq_type == "DNA":
            lines.append(f"- Reverse complement ready")
        lines.append("")

    return "\n".join(lines)
