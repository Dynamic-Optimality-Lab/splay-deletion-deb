"""SA-04 verdict composition + H1 untouched-claim rules (production helpers).

EV-8 (contaminated n8 validation) is mandatory but never sufficient for UH-6:
UH-6_PASS_FRESH_H1 requires the fresh H1 pass plus independent agreement.
"""
KEEP_PASS = "UH-6_PASS_FRESH_H1"


def uh6_verdict(ev8_verdict, h1_verdict, independent_agreement):
    """Compose the corrected UH-6 outcome.

    ev8_verdict / h1_verdict in {"PASS", "REJECTED"}.
    independent_agreement bool covers BOTH validations.
    """
    if ev8_verdict == "REJECTED" or h1_verdict == "REJECTED":
        return "REJECTED"
    if ev8_verdict == "PASS" and h1_verdict == "PASS" and independent_agreement:
        return KEEP_PASS
    if ev8_verdict == "PASS" and h1_verdict != "PASS":
        return "REJECTED (H1 missing/failing: EV-8 alone never discharges UH-6)"
    return "REJECTED"


H1_SIZES = (9, 10, 12, 16, 24, 32)


def h1_untouched_claim_valid(untouched_sizes, h1_revealed):
    """H1 fresh-holdout claim rule. Empty claims are vacuously valid. 7 is
    never claimable (SA-03 era rule). H1 sizes are claimable only while
    genuinely unrevealed. Unknown future sizes are left to future protocols
    (returned True here; a new protocol must still ratify them)."""
    sizes = list(untouched_sizes or [])
    if not sizes:
        return True
    if 7 in sizes:
        return False
    if h1_revealed and any(s in H1_SIZES for s in sizes):
        return False
    return True
