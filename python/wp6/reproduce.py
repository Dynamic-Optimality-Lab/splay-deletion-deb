"""S01 clean reproduction (SPEC 18, WP-6).

Fresh checkout via `git worktree add` at the sealed HEAD; rebuild the
deterministic WP-1 layer (trees + transitions + reachability, n=2..6) with
frozen deps; compare byte-identical against this checkout (logical-JSON
fallback recorded per file if encoder bytes ever differ); verify the sealed
n=7 certificates with the independent verifier; recompute FINAL_RESULT.json
from artifacts and compare identical. Emits artifacts/logs/reproduce.json.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


# console.log equivalent [WP6-REP-01]: reproduce module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


WORKTREE = os.path.join("C:\\", "Users", "SAIFMA~1", "AppData", "Local", "Temp",
                         "opencode", "wp6repro")
SIZES = (2, 3, 4, 5, 6)


def sha(path):
    """SHA-256 of a file (streamed)."""
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def logical_equal(path_a, path_b):
    """Compare decompressed logical JSON (encoder-byte fallback)."""
    import zstandard as zstd
    for path in (path_a, path_b):
        if not os.path.exists(path):
            return False
    with open(path_a, "rb") as handle:
        raw_a = handle.read()
    with open(path_b, "rb") as handle:
        raw_b = handle.read()
    try:
        dec_a = zstd.ZstdDecompressor().decompress(raw_a)
        dec_b = zstd.ZstdDecompressor().decompress(raw_b)
        return json.loads(dec_a) == json.loads(dec_b)
    except Exception:
        return raw_a == raw_b


def fresh_checkout():
    """Create a fresh worktree checkout at HEAD."""
    # console.log equivalent [WP6-REP-02]: fresh checkout begin.
    console_log("WP6-REP-02", "fresh worktree checkout begin")
    if os.path.exists(WORKTREE):
        subprocess.run(["git", "worktree", "remove", "--force", WORKTREE],
                       cwd=REPO, capture_output=True)
        shutil.rmtree(WORKTREE, ignore_errors=True)
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                       capture_output=True, text=True)
    head = r.stdout.strip()
    r = subprocess.run(["git", "worktree", "add", WORKTREE, head],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("worktree add failed: %s" % r.stderr[-500:])
    # console.log equivalent [WP6-REP-02]: checkout HEAD emission.
    console_log("WP6-REP-02", "fresh checkout at %s" % head)
    return head


def rebuild_and_compare():
    """Rebuild n=2..6 deterministic layer in the worktree; compare."""
    # console.log equivalent [WP6-REP-03]: rebuild + compare per n.
    console_log("WP6-REP-03", "worktree rebuild n=2..6 begin")
    rows = []
    for n in SIZES:
        out_trees = os.path.join(WORKTREE, "repro_out", "trees%d" % n)
        out_trans = os.path.join(WORKTREE, "repro_out", "trans%d" % n)
        out_reach = os.path.join(WORKTREE, "repro_out", "reach%d" % n)
        for d in (out_trees, out_trans, out_reach):
            os.makedirs(d, exist_ok=True)
        r = subprocess.run(
            [sys.executable, os.path.join(WORKTREE, "python", "reference", "enumerate.py"),
             "--n", str(n), "--out", out_trees], capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError("worktree enumerate n=%d failed" % n)
        r = subprocess.run(
            [sys.executable, os.path.join(WORKTREE, "python", "reference", "pair_graph.py"),
             "--n", str(n), "--transitions-out", out_trans,
             "--reachability-out", out_reach], capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError("worktree pair_graph n=%d failed" % n)
        pairs = [("trees", out_trees, "trees.jsonl.zst",
                  os.path.join(REPO, "artifacts", "trees", "n%d" % n, "trees.jsonl.zst")),
                 ("transitions", out_trans, "forward.bin.zst",
                  os.path.join(REPO, "artifacts", "transitions", "n%d" % n, "forward.bin.zst")),
                 ("reachability", out_reach, "reachable.json.zst",
                  os.path.join(REPO, "artifacts", "reachability", "n%d" % n, "reachable.json.zst"))]
        for kind, outd, name, ref in pairs:
            got = os.path.join(outd, name)
            if not os.path.exists(got):
                got = [os.path.join(outd, f) for f in os.listdir(outd)][0]
            byte_same = sha(got) == sha(ref)
            method = "byte-identical" if byte_same else (
                "logical-identical" if logical_equal(got, ref) else "MISMATCH")
            rows.append({"n": n, "kind": kind, "method": method})
            # console.log equivalent [WP6-REP-03]: per-artifact verdict emission.
            console_log("WP6-REP-03", "n=%d %s %s" % (n, kind, method))
    return rows


def verify_n7_and_result():
    """Independent n=7 cert verification + FINAL_RESULT recompute."""
    # console.log equivalent [WP6-REP-04]: n=7 verification + recompute.
    console_log("WP6-REP-04", "sealed n=7 verification + result recompute")
    outd = os.path.join(REPO, "artifacts", "wp6", "reverify", "n7")
    os.makedirs(outd, exist_ok=True)
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, "python", "audit", "verify_bn_certificate.py"),
         "--n", "7", "--cert-dir", os.path.join(REPO, "artifacts", "certificates", "n7"),
         "--out", outd], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    n7_ok = (r.returncode == 0)
    from python.wp6 import seal as SEAL
    recomputed = SEAL.build_result()
    with open(os.path.join(REPO, "artifacts", "seal", "FINAL_RESULT.json"),
              encoding="utf-8") as handle:
        filed = json.load(handle)
    result_ok = (recomputed == filed)
    # console.log equivalent [WP6-REP-04]: verification verdict emission.
    console_log("WP6-REP-04", "n7 cert verify=%s result recompute=%s" % (n7_ok, result_ok))
    return n7_ok, result_ok


def main(argv=None):
    """S01 reproduction pipeline."""
    t0 = time.time()
    # console.log equivalent [WP6-REP-05]: pipeline start.
    console_log("WP6-REP-05", "S01 clean reproduction start")
    head = fresh_checkout()
    try:
        rows = rebuild_and_compare()
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", WORKTREE],
                       cwd=REPO, capture_output=True)
        shutil.rmtree(WORKTREE, ignore_errors=True)
    n7_ok, result_ok = verify_n7_and_result()
    verdict = ("PASS" if all(r["method"] != "MISMATCH" for r in rows)
               and n7_ok and result_ok else "FAIL")
    log = {"experiment_id": "SPLAY-AM-PD-v0.1", "phase": "S01",
           "fresh_checkout_head": head, "rebuild": rows,
           "n7_cert_verify": n7_ok, "result_recompute_identical": result_ok,
           "verdict": verdict, "wall_seconds": round(time.time() - t0, 1)}
    with open(os.path.join(REPO, "artifacts", "logs", "reproduce.json"),
              "w", encoding="utf-8") as handle:
        json.dump(log, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP6-REP-06]: pipeline verdict.
    console_log("WP6-REP-06", "S01 reproduction %s" % verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
