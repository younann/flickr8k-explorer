"""Deterministic, local-only analysis primitives for imported captions and images."""

from dataclasses import dataclass
from itertools import combinations
import re
from statistics import fmean, pstdev

from PIL import Image


@dataclass(frozen=True)
class CaptionAnalysis:
    disagreement_score: int
    token_disagreement: float
    vocabulary_diversity: float
    mean_caption_length: float
    caption_length_spread: float


def _tokens(caption: str) -> list[str]:
    return re.findall(r"[a-z]+", caption.lower())


def caption_analysis(captions: list[str]) -> CaptionAnalysis:
    token_lists = [_tokens(caption) for caption in captions]
    lengths = [len(tokens) for tokens in token_lists]
    token_sets = [set(tokens) for tokens in token_lists]

    distances: list[float] = []
    for left, right in combinations(token_sets, 2):
        union = left | right
        distances.append(1.0 - (len(left & right) / len(union) if union else 1.0))
    token_disagreement = fmean(distances) if distances else 0.0

    all_tokens = [token for tokens in token_lists for token in tokens]
    vocabulary_diversity = len(set(all_tokens)) / len(all_tokens) if all_tokens else 0.0
    mean_length = fmean(lengths) if lengths else 0.0
    length_spread = pstdev(lengths) if len(lengths) > 1 else 0.0

    # Vocabulary diversity modulates pairwise variation, so identical caption
    # sets retain the established zero score while both agreed signals matter.
    score = round(100 * token_disagreement * (0.7 + 0.3 * vocabulary_diversity))
    return CaptionAnalysis(
        disagreement_score=max(0, min(100, score)),
        token_disagreement=token_disagreement,
        vocabulary_diversity=vocabulary_diversity,
        mean_caption_length=mean_length,
        caption_length_spread=length_spread,
    )


def perceptual_hash(image: Image.Image) -> int:
    """Return an 8x8 average hash as an integer (row-major, MSB first)."""
    grayscale = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
    pixels = list(grayscale.getdata())
    mean = fmean(pixels)
    result = 0
    for pixel in pixels:
        result = (result << 1) | int(pixel >= mean)
    return result


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()
