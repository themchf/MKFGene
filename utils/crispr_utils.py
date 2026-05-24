"""
utils/crispr_utils.py
CRISPR guide RNA detection and scoring utilities.
"""

import re
import random
from typing import Dict, List

# ── PAM System Definitions ────────────────────────────────────────
PAM_SYSTEMS: Dict[str, Dict] = {
    "SpCas9": {
        "label":       "SpCas9 (NGG)",
        "pam":         "NGG",
        "pam_pattern": r"(?=[ACGT]{20}[ACGT]GG)",
        "guide_len":   20,
        "description": "Most widely used; 3' NGG PAM; high efficiency",
        "cut_offset":  -3,
    },
    "SaCas9": {
        "label":       "SaCas9 (NNGRRT)",
        "pam":         "NNGRRT",
        "pam_pattern": r"(?=[ACGT]{21}[ACGT]{2}G[AG]{2}T)",
        "guide_len":   21,
        "description": "Smaller; useful for AAV delivery; 3' NNGRRT PAM",
        "cut_offset":  -3,
    },
    "Cas12a": {
        "label":       "Cas12a / Cpf1 (TTTV)",
        "pam":         "TTTV",
        "pam_pattern": r"(?=TTT[ACG][ACGT]{23})",
        "guide_len":   23,
        "description": "5' TTTV PAM; staggered cut; T-rich targets",
        "cut_offset":  18,
    },
    "SpRY": {
        "label":       "SpRY (NRN/NYN)",
        "pam":         "NRN",
        "pam_pattern": r"(?=[ACGT]{20}[ACGT][AG][ACGT])",
        "guide_len":   20,
        "description": "Near-PAMless; broadest target range",
        "cut_offset":  -3,
    },
    "BE3_CBE": {
        "label":       "BE3 Base Editor (NGG)",
        "pam":         "NGG",
        "pam_pattern": r"(?=[ACGT]{20}[ACGT]GG)",
        "guide_len":   20,
        "description": "C→T base editing; editing window positions 4–8",
        "cut_offset":  None,
    },
}


def find_pam_sites(seq: str, system: str = "SpCas9") -> List[Dict]:
    """
    Scan both strands of seq for PAM-adjacent guide RNA candidates.
    Returns list of dicts with guide, pam_seq, position, strand.
    """
    config = PAM_SYSTEMS.get(system, PAM_SYSTEMS["SpCas9"])
    guide_len = config["guide_len"]
    seq = seq.upper()
    rc  = _reverse_complement(seq)
    results = []

    for strand_label, strand_seq, offset_fn in [
        ("+", seq, lambda pos: pos),
        ("-", rc,  lambda pos: len(seq) - pos - guide_len),
    ]:
        if system == "Cas12a":
            # 5' PAM: find TTT[ACG] then take next guide_len nt
            for m in re.finditer(r"TTT[ACG]", strand_seq):
                start = m.end()
                if start + guide_len <= len(strand_seq):
                    guide   = strand_seq[start:start + guide_len]
                    pam_seq = strand_seq[m.start():m.end()]
                    if _is_valid_guide(guide):
                        results.append({
                            "guide":    guide,
                            "pam_seq":  pam_seq,
                            "position": offset_fn(start),
                            "strand":   strand_label,
                        })
        else:
            # 3' PAM: take guide_len nt upstream of NGG / pattern
            for m in re.finditer(r"[ACGT]GG", strand_seq):
                start = m.start() - guide_len
                if start >= 0:
                    guide   = strand_seq[start:m.start()]
                    pam_seq = strand_seq[m.start():m.start()+3]
                    if _is_valid_guide(guide):
                        results.append({
                            "guide":    guide,
                            "pam_seq":  pam_seq,
                            "position": offset_fn(start),
                            "strand":   strand_label,
                        })

    # Deduplicate by (guide, strand)
    seen = set()
    unique = []
    for r in results:
        key = (r["guide"], r["strand"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


def score_guide_rna(guide: str, system: str = "SpCas9") -> int:
    """
    Heuristic on-target score (0–100).
    Based on: GC content, homopolymer penalty, seed region quality, length.
    Not a replacement for validated tools (Doench/Rule Set 2, etc.).
    """
    guide = guide.upper()
    if len(guide) < 10:
        return 0

    score = 60  # baseline

    # GC content (ideal 40–70%)
    gc = (guide.count("G") + guide.count("C")) / len(guide) * 100
    if 40 <= gc <= 70:
        score += 15
    elif 30 <= gc <= 80:
        score += 5
    else:
        score -= 15

    # Homopolymer penalty (≥4 identical bases)
    if re.search(r"(.)\1{3,}", guide):
        score -= 20

    # Avoid TTTT (Pol III terminator)
    if "TTTT" in guide:
        score -= 15

    # Seed region (last 12 nt for SpCas9/3'PAM, first 12 for Cas12a)
    seed = guide[-12:] if system != "Cas12a" else guide[:12]
    seed_gc = (seed.count("G") + seed.count("C")) / len(seed) * 100
    if 40 <= seed_gc <= 65:
        score += 10

    # Slight bonus for G at position 20 (SpCas9)
    if system in ("SpCas9", "SpRY", "BE3_CBE") and guide[-1] == "G":
        score += 5

    # Add deterministic noise based on guide sequence for realism
    h = sum(ord(c) * (i + 1) for i, c in enumerate(guide))
    score += (h % 11) - 5

    return max(0, min(100, score))


def predict_edit_outcome(guide: str, edit_type: str) -> Dict:
    """High-level conceptual edit outcome prediction."""
    outcomes = {
        "Knockout (NHEJ)": {
            "mechanism":    "Non-homologous end joining introduces indels at cut site",
            "expected":     "Frameshift or in-frame deletion → loss-of-function",
            "efficiency":   "Typically 30–80% in mammalian cells",
            "reversibility":"Irreversible (mosaic outcomes possible)",
        },
        "Knock-in (HDR)": {
            "mechanism":    "Homology-directed repair using supplied donor template",
            "expected":     "Precise sequence insertion or substitution",
            "efficiency":   "Typically 1–20%; higher in dividing cells",
            "reversibility":"Irreversible",
        },
        "Base Editing (CBE)": {
            "mechanism":    "Cytosine deaminase converts C→U→T within editing window",
            "expected":     "C·G → T·A transition at positions 4–8 of guide",
            "efficiency":   "Typically 20–60% per allele",
            "reversibility":"Irreversible",
        },
        "Base Editing (ABE)": {
            "mechanism":    "Adenine deaminase converts A→I→G within editing window",
            "expected":     "A·T → G·C transition at positions 4–7 of guide",
            "efficiency":   "Typically 30–70% per allele",
            "reversibility":"Irreversible",
        },
        "Prime Editing": {
            "mechanism":    "Reverse transcriptase writes new sequence from pegRNA template",
            "expected":     "Precise insertion, deletion, or all 12 possible transversions",
            "efficiency":   "Typically 5–50%; highly target-dependent",
            "reversibility":"Irreversible",
        },
    }
    return outcomes.get(edit_type, {"mechanism": "Unknown", "expected": "N/A", "efficiency": "N/A", "reversibility": "N/A"})


# ── Internal helpers ──────────────────────────────────────────────

def _is_valid_guide(guide: str) -> bool:
    return bool(guide) and len(guide) >= 18 and all(c in "ACGT" for c in guide)


def _reverse_complement(seq: str) -> str:
    comp = str.maketrans("ACGT", "TGCA")
    return seq.upper().translate(comp)[::-1]
