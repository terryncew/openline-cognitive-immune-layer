#!/usr/bin/env python3
"""
Active Recursive Boundary Controller Test.

This is a toy-system audit, not a consciousness proof.

Question:
    Does preserving a prior boundary record and using it as a controller
    improve future boundary-crossing regulation?

Data:
    Verified 400k U(2,3) and U(3,4) accepted prefixes.

Controllers:
    1. no_memory_baseline
       No boundary record. It can only route a fixed fraction of candidate crossings,
       chosen randomly under repeated controls.

    2. receipt_memory_controller
       Uses the previous 50k-window survivor self-shadow as a boundary receipt.
       It routes/blocks candidates whose phase falls in the highest-risk bins.

Evaluation:
    On the next 50k-window candidate interval, compare:
       - unsafe_rejection_capture_rate: fraction of true rejected reachable candidates routed
       - accepted_false_block_rate: fraction of true accepted candidates routed
       - precision: routed candidates that were true rejected reachable
       - enrichment over base rejection rate
       - controller utility under a simple cost model

Important boundary:
    In Ulam, a high-risk controller can look very strong because accepted terms
    almost never enter the predicted wall. That is exactly why this is a clean toy
    demonstration, not a general consciousness claim.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List
import argparse, hashlib, json, math, time, zipfile
import numpy as np

TAU = 2*math.pi
BINS = 720
COUNT = 400000
WINDOW_TERMS = 50000
ROUTE_FRAC = 0.10

SEEDS = {
    "U(2,3)": {
        "seed": [2,3],
        "alpha": 1.165012873891295,
        "values": "input/u23/data/ulam_2_3_values_400000.bin",
    },
    "U(3,4)": {
        "seed": [3,4],
        "alpha": 2.209039570339974,
        "values": "input/u34/data/ulam_3_4_values_400000.bin",
    },
}

@dataclass
class Receipt:
    claim: str
    action: str
    evidence: Dict[str, Any]
    result: str
    witness: str = "active-recursive-boundary-controller"
    parent_hash: str | None = None
    receipt_hash: str | None = None
    def seal(self):
        body = {
            "claim": self.claim,
            "action": self.action,
            "evidence": self.evidence,
            "result": self.result,
            "witness": self.witness,
            "parent_hash": self.parent_hash,
        }
        self.receipt_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",",":")).encode()).hexdigest()
        return self

receipts: List[Receipt] = []

def add_receipt(claim, action, evidence, result):
    parent = receipts[-1].receipt_hash if receipts else None
    receipts.append(Receipt(claim, action, evidence, result, parent_hash=parent).seal())

def write_receipts(path: Path):
    with path.open("w", encoding="utf-8") as f:
        for r in receipts:
            f.write(json.dumps(asdict(r), sort_keys=True) + "\n")

def verify_receipts(path: Path) -> bool:
    prev = None
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if r["parent_hash"] != prev:
            return False
        body = {
            "claim": r["claim"],
            "action": r["action"],
            "evidence": r["evidence"],
            "result": r["result"],
            "witness": r["witness"],
            "parent_hash": r["parent_hash"],
        }
        h = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",",":")).encode()).hexdigest()
        if h != r["receipt_hash"]:
            return False
        prev = h
    return True

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def exact_counts(values: np.ndarray) -> np.ndarray:
    max_v = int(values[-1])
    indicator = np.zeros(max_v + 1, dtype=np.float64)
    indicator[values] = 1.0
    conv_len = 2*max_v + 1
    fft_len = 1 << (conv_len - 1).bit_length()
    spec = np.fft.rfft(indicator, n=fft_len)
    conv = np.fft.irfft(spec*spec, n=fft_len)[:conv_len]
    ordered = np.rint(conv).astype(np.int64)
    self_pairs = np.zeros(conv_len, dtype=np.int64)
    self_pairs[values*2] = 1
    out = (ordered - self_pairs)//2
    out[out < 0] = 0
    return out

def phase_bins(n: np.ndarray, alpha: float, bins: int=BINS) -> np.ndarray:
    phases = (n.astype(np.float64)*alpha) % TAU
    idx = np.floor(phases/TAU*bins).astype(np.int64)
    idx[idx == bins] = bins - 1
    return idx

def smooth(x: np.ndarray, radius:int=3) -> np.ndarray:
    y = np.zeros_like(x, dtype=float)
    for k in range(-radius, radius+1):
        y += np.roll(x, k)
    return y/(2*radius+1)

def zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    s = np.std(x)
    return (x-np.mean(x))/(s if s > 0 else 1.0)

def boundary_record(values_window: np.ndarray, alpha: float) -> np.ndarray:
    idx = phase_bins(values_window, alpha)
    h = np.bincount(idx, minlength=BINS).astype(float)
    conv = np.real(np.fft.ifft(np.fft.fft(h)*np.fft.fft(h)))
    conv[conv < 0] = 0
    return zscore(smooth(np.log1p(conv), 3))

def top_mask(score: np.ndarray, frac: float=ROUTE_FRAC) -> np.ndarray:
    k = max(1, int(round(len(score)*frac)))
    order = np.argsort(score)[::-1]
    mask = np.zeros(len(score), dtype=bool)
    mask[order[:k]] = True
    return mask

def evaluate_route(route_mask_for_candidates: np.ndarray, candidates: np.ndarray, R: np.ndarray, accepted: np.ndarray) -> Dict[str, Any]:
    cand_R = R[candidates]
    reachable = cand_R >= 1
    rejected = cand_R >= 2
    is_acc = accepted[candidates]
    routed = route_mask_for_candidates

    routed_count = int(routed.sum())
    true_rejected = int((reachable & rejected).sum())
    true_accepted = int(is_acc.sum())

    captured_rejected = int((routed & reachable & rejected).sum())
    false_blocked_accepted = int((routed & is_acc).sum())

    routed_rejected = int((routed & reachable & rejected).sum())
    routed_accepted = int((routed & is_acc).sum())
    routed_reachable = int((routed & reachable).sum())

    base_rejection_rate = float((reachable & rejected).sum()/reachable.sum()) if reachable.sum() else float("nan")
    routed_rejection_rate = float((routed & reachable & rejected).sum()/(routed & reachable).sum()) if (routed & reachable).sum() else float("nan")

    # Utility: catch rejected reachable candidate = +1; false-block accepted = -10.
    # This deliberately makes false positives expensive.
    utility = captured_rejected - 10*false_blocked_accepted

    return {
        "candidate_count": int(len(candidates)),
        "reachable_count": int(reachable.sum()),
        "accepted_count": true_accepted,
        "rejected_reachable_count": true_rejected,
        "routed_count": routed_count,
        "routed_reachable_count": routed_reachable,
        "captured_rejected_count": captured_rejected,
        "false_blocked_accepted_count": false_blocked_accepted,
        "unsafe_rejection_capture_rate": float(captured_rejected/true_rejected) if true_rejected else float("nan"),
        "accepted_false_block_rate": float(false_blocked_accepted/true_accepted) if true_accepted else float("nan"),
        "precision_rejected_given_routed_reachable": float(routed_rejected/routed_reachable) if routed_reachable else float("nan"),
        "base_rejection_rate_reachable": base_rejection_rate,
        "routed_rejection_rate_reachable": routed_rejection_rate,
        "enrichment_over_base": float(routed_rejection_rate/base_rejection_rate) if base_rejection_rate and base_rejection_rate > 0 else float("nan"),
        "utility": int(utility),
    }

def analyze_seed(root: Path, name: str, cfg: Dict[str,Any]) -> Dict[str,Any]:
    values_path = root/cfg["values"]
    if not values_path.exists():
        return {"name":name, "status":"missing_values", "path":str(values_path)}
    values = np.fromfile(values_path, dtype=np.int64)
    if len(values) < COUNT:
        return {"name":name, "status":"insufficient_values", "count":int(len(values))}
    values = values[:COUNT]
    alpha = float(cfg["alpha"])

    add_receipt(f"{name} values loaded for active controller test.", "load_values", {"sha256":sha256_file(values_path), "count":int(len(values)), "last_value":int(values[-1])}, "support")

    R = exact_counts(values)
    R_hash = hashlib.sha256(R.tobytes()).hexdigest()
    add_receipt(f"{name} representation depths recomputed.", "exact_counts", {"R_len":int(len(R)), "R_sha256":R_hash, "R_max":int(R.max())}, "support")

    max_v = int(values[-1])
    accepted = np.zeros(max_v+1, dtype=bool)
    accepted[values] = True

    rng = np.random.default_rng(202)

    rows = []
    for t in range(0, COUNT-WINDOW_TERMS, WINDOW_TERMS):
        source_values = values[t:t+WINDOW_TERMS]
        target_hi = int(values[t+2*WINDOW_TERMS-1]) if t+2*WINDOW_TERMS <= COUNT else int(values[t+WINDOW_TERMS-1])
        source_hi = int(values[t+WINDOW_TERMS-1])
        if t+2*WINDOW_TERMS > COUNT:
            break

        candidates = np.arange(source_hi+1, target_hi+1, dtype=np.int64)
        idx = phase_bins(candidates, alpha)

        score = boundary_record(source_values, alpha)
        wall = top_mask(score)
        receipt_route = wall[idx]
        receipt_eval = evaluate_route(receipt_route, candidates, R, accepted)

        # no-memory random baselines: same route fraction, no boundary record.
        random_evals = []
        for k in range(50):
            random_route = rng.random(len(candidates)) < ROUTE_FRAC
            random_evals.append(evaluate_route(random_route, candidates, R, accepted))

        # no-memory phase-bin random wall: route same number of phase bins but no learned record.
        phase_random_evals = []
        for k in range(50):
            bins = np.zeros(BINS, dtype=bool)
            chosen = rng.choice(BINS, size=int(round(BINS*ROUTE_FRAC)), replace=False)
            bins[chosen] = True
            phase_random_evals.append(evaluate_route(bins[idx], candidates, R, accepted))

        def mean_metric(evals, key):
            arr = np.array([e[key] for e in evals], dtype=float)
            return float(np.nanmean(arr))
        def max_metric(evals, key):
            arr = np.array([e[key] for e in evals], dtype=float)
            return float(np.nanmax(arr))

        row = {
            "source_terms": [t+1, t+WINDOW_TERMS],
            "target_terms": [t+WINDOW_TERMS+1, t+2*WINDOW_TERMS],
            "source_value_hi": source_hi,
            "target_value_hi": target_hi,
            "receipt_memory": receipt_eval,
            "no_memory_random_mean": {
                "unsafe_rejection_capture_rate": mean_metric(random_evals, "unsafe_rejection_capture_rate"),
                "accepted_false_block_rate": mean_metric(random_evals, "accepted_false_block_rate"),
                "precision_rejected_given_routed_reachable": mean_metric(random_evals, "precision_rejected_given_routed_reachable"),
                "enrichment_over_base": mean_metric(random_evals, "enrichment_over_base"),
                "utility": mean_metric(random_evals, "utility"),
            },
            "no_memory_random_max": {
                "precision_rejected_given_routed_reachable": max_metric(random_evals, "precision_rejected_given_routed_reachable"),
                "enrichment_over_base": max_metric(random_evals, "enrichment_over_base"),
                "utility": max_metric(random_evals, "utility"),
            },
            "no_memory_random_phase_bins_mean": {
                "unsafe_rejection_capture_rate": mean_metric(phase_random_evals, "unsafe_rejection_capture_rate"),
                "accepted_false_block_rate": mean_metric(phase_random_evals, "accepted_false_block_rate"),
                "precision_rejected_given_routed_reachable": mean_metric(phase_random_evals, "precision_rejected_given_routed_reachable"),
                "enrichment_over_base": mean_metric(phase_random_evals, "enrichment_over_base"),
                "utility": mean_metric(phase_random_evals, "utility"),
            },
            "no_memory_random_phase_bins_max": {
                "precision_rejected_given_routed_reachable": max_metric(phase_random_evals, "precision_rejected_given_routed_reachable"),
                "enrichment_over_base": max_metric(phase_random_evals, "enrichment_over_base"),
                "utility": max_metric(phase_random_evals, "utility"),
            },
        }
        rows.append(row)

    def avg_path(path):
        vals = []
        for r in rows:
            cur = r
            for p in path:
                cur = cur[p]
            vals.append(cur)
        return float(np.nanmean(np.array(vals, dtype=float)))
    def min_path(path):
        vals = []
        for r in rows:
            cur = r
            for p in path:
                cur = cur[p]
            vals.append(cur)
        return float(np.nanmin(np.array(vals, dtype=float)))

    summary = {
        "name": name,
        "seed": cfg["seed"],
        "alpha": alpha,
        "status": "analyzed",
        "window_terms": WINDOW_TERMS,
        "transition_count": len(rows),
        "values_sha256": sha256_file(values_path),
        "representation_depth_sha256": R_hash,
        "receipt_memory_capture_mean": avg_path(["receipt_memory","unsafe_rejection_capture_rate"]),
        "receipt_memory_capture_min": min_path(["receipt_memory","unsafe_rejection_capture_rate"]),
        "receipt_memory_false_block_mean": avg_path(["receipt_memory","accepted_false_block_rate"]),
        "receipt_memory_false_block_max": float(np.nanmax([r["receipt_memory"]["accepted_false_block_rate"] for r in rows])),
        "receipt_memory_precision_mean": avg_path(["receipt_memory","precision_rejected_given_routed_reachable"]),
        "receipt_memory_enrichment_mean": avg_path(["receipt_memory","enrichment_over_base"]),
        "receipt_memory_utility_mean": avg_path(["receipt_memory","utility"]),
        "random_baseline_precision_mean": avg_path(["no_memory_random_mean","precision_rejected_given_routed_reachable"]),
        "phase_random_baseline_precision_mean": avg_path(["no_memory_random_phase_bins_mean","precision_rejected_given_routed_reachable"]),
        "random_baseline_enrichment_mean": avg_path(["no_memory_random_mean","enrichment_over_base"]),
        "phase_random_baseline_enrichment_mean": avg_path(["no_memory_random_phase_bins_mean","enrichment_over_base"]),
        "random_baseline_utility_mean": avg_path(["no_memory_random_mean","utility"]),
        "phase_random_baseline_utility_mean": avg_path(["no_memory_random_phase_bins_mean","utility"]),
        "rows": rows,
    }

    # Conservative verdict.
    if (
        summary["receipt_memory_precision_mean"] > 0.98 and
        summary["receipt_memory_false_block_max"] < 0.01 and
        summary["receipt_memory_enrichment_mean"] > summary["phase_random_baseline_enrichment_mean"] + 0.10 and
        summary["receipt_memory_utility_mean"] > summary["phase_random_baseline_utility_mean"] * 1.5
    ):
        verdict = "active_recursive_boundary_control_supported"
    elif (
        summary["receipt_memory_precision_mean"] > summary["phase_random_baseline_precision_mean"] and
        summary["receipt_memory_utility_mean"] > summary["phase_random_baseline_utility_mean"]
    ):
        verdict = "active_recursive_boundary_control_partial"
    else:
        verdict = "active_recursive_boundary_control_not_supported"
    summary["verdict"] = verdict

    add_receipt(f"{name} active recursive boundary controller audit completed.", "active_controller", {"capture_mean":summary["receipt_memory_capture_mean"], "false_block_mean":summary["receipt_memory_false_block_mean"], "precision_mean":summary["receipt_memory_precision_mean"], "enrichment_mean":summary["receipt_memory_enrichment_mean"], "verdict":verdict}, "support")
    return summary

def write_md(root: Path, report: Dict[str,Any]):
    md = """# Active Recursive Boundary Controller Test

## Purpose

This is the next test after nested boundary closure.

The previous test asked whether a boundary record from one window predicts the next window.

This test asks whether using that prior boundary record as a controller improves future crossing regulation.

It is still a toy-system audit. It does not prove consciousness.

## Controller setup

No-memory controller:

- no prior boundary record
- routes the same fraction of candidate crossings randomly

Receipt-memory controller:

- preserves the prior 50k-window boundary record
- uses that record to route/block high-risk phase regions in the next 50k-window candidate interval

## Summary

| Seed | verdict | capture mean | false-block mean | precision mean | enrichment mean | utility mean | phase-random utility mean |
|---|---|---:|---:|---:|---:|---:|---:|
"""
    for r in report["results"]:
        if r.get("status") != "analyzed":
            md += f"| {r['name']} | {r.get('status')} | - | - | - | - | - | - |\n"
            continue
        md += f"| {r['name']} | {r['verdict']} | {r['receipt_memory_capture_mean']:.6f} | {r['receipt_memory_false_block_mean']:.6f} | {r['receipt_memory_precision_mean']:.6f} | {r['receipt_memory_enrichment_mean']:.6f} | {r['receipt_memory_utility_mean']:.1f} | {r['phase_random_baseline_utility_mean']:.1f} |\n"

    md += """

## Read

A positive result means:

A preserved boundary record can be used to regulate future crossings better than a no-memory controller.

That is active recursive boundary regulation in a deterministic toy system.

It does not prove consciousness. The consciousness-adjacent claim remains smaller:

A system becomes more complex when records of prior crossings are preserved and used to decide future crossings.

## Honest boundary

This test is strong inside Ulam because the Ulam rule gives exact accepted/rejected labels.

The result does not automatically transfer to biology, neuroscience, AI agents, institutions, or cosmology.

To transfer it, those systems need explicit boundary events, explicit allowed/rejected labels, and real receipt records.
"""
    (root/"ACTIVE_RECURSIVE_BOUNDARY_CONTROLLER_TEST.md").write_text(md, encoding="utf-8")

def write_svg(root: Path, report: Dict[str,Any]):
    rows = [r for r in report["results"] if r.get("status")=="analyzed"]
    w,h=940,520
    left,right,top,bottom=100,50,60,80
    plot_h=300
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>']
    svg.append(f'<text x="{left}" y="32" font-family="Arial" font-size="18">Active recursive boundary control: receipt memory vs no memory</text>')
    labels=["precision","false-block","enrichment"]
    for panel_idx,label in enumerate(labels):
        x0=left+panel_idx*((w-left-right)/3)
        pw=(w-left-right)/3-25
        svg.append(f'<text x="{x0}" y="{top-10}" font-family="Arial" font-size="12">{label}</text>')
        svg.append(f'<line x1="{x0}" y1="{top+plot_h}" x2="{x0+pw}" y2="{top+plot_h}" stroke="#222"/>')
        for i,r in enumerate(rows):
            if label=="precision":
                mem=r["receipt_memory_precision_mean"]; base=r["phase_random_baseline_precision_mean"]; ymax=1.0
            elif label=="false-block":
                mem=r["receipt_memory_false_block_mean"]; base=0.10; ymax=0.12
            else:
                mem=r["receipt_memory_enrichment_mean"]; base=r["phase_random_baseline_enrichment_mean"]; ymax=max(1.5, mem*1.1)
            bx=x0+30+i*90
            mem_h=min(plot_h, mem/ymax*plot_h)
            base_h=min(plot_h, base/ymax*plot_h)
            svg.append(f'<rect x="{bx}" y="{top+plot_h-base_h:.1f}" width="28" height="{base_h:.1f}" fill="#aaa"/>')
            svg.append(f'<rect x="{bx+34}" y="{top+plot_h-mem_h:.1f}" width="28" height="{mem_h:.1f}" fill="#333"/>')
            svg.append(f'<text x="{bx}" y="{top+plot_h+18}" font-family="Arial" font-size="10">{r["name"]}</text>')
    svg.append(f'<text x="{left}" y="{h-35}" font-family="Arial" font-size="12">light = no-memory phase-random baseline; dark = receipt-memory controller</text>')
    svg.append('</svg>')
    (root/"active_recursive_boundary_controller.svg").write_text("\n".join(svg), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    add_receipt("Active recursive boundary controller test started.", "start", {"seeds":list(SEEDS.keys()), "window_terms":WINDOW_TERMS, "route_fraction":ROUTE_FRAC}, "support")
    results = []
    for name,cfg in SEEDS.items():
        results.append(analyze_seed(root, name, cfg))

    report = {
        "verdict": "active_recursive_boundary_controller_test_completed",
        "boundary": "Toy-system active-controller audit only. Does not prove consciousness.",
        "results": results,
        "created_at_unix": int(time.time())
    }

    receipt_path = root/"active_recursive_boundary_controller_receipts.jsonl"
    write_receipts(receipt_path)
    report["receipt_chain_valid"] = verify_receipts(receipt_path)

    (root/"active_recursive_boundary_controller_report.json").write_text(json.dumps(report, indent=2, allow_nan=True), encoding="utf-8")
    summary=[]
    keep=["name","seed","alpha","verdict","receipt_memory_capture_mean","receipt_memory_capture_min","receipt_memory_false_block_mean","receipt_memory_false_block_max","receipt_memory_precision_mean","receipt_memory_enrichment_mean","receipt_memory_utility_mean","phase_random_baseline_precision_mean","phase_random_baseline_enrichment_mean","phase_random_baseline_utility_mean"]
    for r in results:
        if r.get("status")=="analyzed":
            summary.append({k:r[k] for k in keep})
        else:
            summary.append(r)
    (root/"active_recursive_boundary_controller_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=True), encoding="utf-8")

    write_md(root, report)
    write_svg(root, report)

    zip_path = root.parent/"openline-active-recursive-boundary-controller-test.zip"
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob("*"):
            if p.is_file():
                if "/input/" in str(p):
                    continue
                z.write(p, p.relative_to(root.parent))

    print(json.dumps({
        "verdict": report["verdict"],
        "receipt_chain_valid": report["receipt_chain_valid"],
        "results": summary,
        "zip": str(zip_path)
    }, indent=2, allow_nan=True))

if __name__ == "__main__":
    main()
