"""Candidate-set freeze + manifest hashing helpers (SA-03 §SA-03.7/10).

No synthesis here: pure hash-and-record utilities used by WP-5 later and by
SA-03 freeze tests (temp state only) to prove the freeze-before-unlock and
hash-binding semantics.
"""
import hashlib
import json


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def freeze_candidate_manifest(doc_without_hash):
    """Return (doc_with_sha256, sha256): hash of canonical bytes (no self-embed)."""
    blob = (json.dumps(doc_without_hash, sort_keys=True) + "\n").encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    doc = dict(doc_without_hash)
    doc["sha256"] = digest
    return doc, digest


def new_set_entry(hypothesis_id, sha256, formula_sha256, b_H):
    return {"hypothesis_id": hypothesis_id, "sha256": sha256,
            "formula_sha256": formula_sha256,
            "b_H": {"p": str(b_H[0]), "q": str(b_H[1])}}


def verify_manifest_hash(doc):
    """Recompute-and-compare (SA03-05/06 pattern)."""
    claimed = doc.get("sha256")
    payload = {k: v for k, v in doc.items() if k != "sha256"}
    blob = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(blob).hexdigest() == claimed


def verdict_for(keep_max_scaled, delete_max_scaled, norm_count, nonneg_count):
    """SA-03.8 verdict rule: any positive scaled residual (or any
    normalization/nonnegativity violation) forces REJECTED; otherwise
    UH-6_PASS_FINITE_N8 (finite n8 fact only, never universality)."""
    if norm_count != 0 or nonneg_count != 0:
        return "REJECTED"
    if int(keep_max_scaled) > 0 or int(delete_max_scaled) > 0:
        return "REJECTED"
    return "UH-6_PASS_FINITE_N8"


class RevisionIdentityError(AssertionError):
    pass


def assert_revision_identity(old_doc, new_doc):
    """SA-03 post-n8 revision rule: same hypothesis_id with a changed formula
    hash is forbidden (must take a NEW hypothesis ID). Returns new ID."""
    if old_doc.get("hypothesis_id") == new_doc.get("hypothesis_id"):
        if old_doc.get("formula_sha256", old_doc.get("sha256")) != \
                new_doc.get("formula_sha256", new_doc.get("sha256")):
            raise RevisionIdentityError(
                "post-n8 revision under the same hypothesis_id is forbidden")
    return new_doc.get("hypothesis_id")


def untouched_claim_valid(untouched_sizes, n8_revealed):
    """SA-03 era rule for untouched-size claims. n7 can never be claimed
    untouched by ERA-B work; n8 only while genuinely unrevealed."""
    sizes = list(untouched_sizes or [])
    if 7 in sizes:
        return False
    if 8 in sizes and n8_revealed:
        return False
    return True
