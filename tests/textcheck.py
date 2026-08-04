"""Shared lexical-overlap helper for R-VAL-2 collusion-firewall tests.

A single definition of the 5-token n-gram set so calibration, service-spec, and
service-rubric disjointness checks can't drift apart."""
import re

def ngrams(text: str, n: int = 5) -> set[str]:
    toks = re.findall(r"[a-z']+", text.lower())
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}
