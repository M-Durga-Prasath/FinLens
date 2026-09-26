import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# Fix Windows console encoding for emoji/unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Defaults ──────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_QUERY = "What were the total revenues reported?"
DEFAULT_COLD_RUNS = 5
DEFAULT_WARM_RUNS = 5
DEFAULT_TOP_K = 6
DEFAULT_CANDIDATE_K = 20


def parse_args():
    parser = argparse.ArgumentParser(
        description="Automated RAG pipeline latency benchmark"
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL,
        help=f"Backend base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--session-id", required=True,
        help="Session UUID to query against (must have uploaded documents)"
    )
    parser.add_argument(
        "--query", default=DEFAULT_QUERY,
        help=f"Query string to benchmark (default: '{DEFAULT_QUERY}')"
    )
    parser.add_argument(
        "--cold-runs", type=int, default=DEFAULT_COLD_RUNS,
        help=f"Number of cold-start runs (default: {DEFAULT_COLD_RUNS})"
    )
    parser.add_argument(
        "--warm-runs", type=int, default=DEFAULT_WARM_RUNS,
        help=f"Number of warm runs (default: {DEFAULT_WARM_RUNS})"
    )
    parser.add_argument(
        "--top-k", type=int, default=DEFAULT_TOP_K,
        help=f"Top-K for reranking (default: {DEFAULT_TOP_K})"
    )
    parser.add_argument(
        "--candidate-k", type=int, default=DEFAULT_CANDIDATE_K,
        help=f"Candidate-K for retrieval (default: {DEFAULT_CANDIDATE_K})"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output Markdown file path (default: latency_report_<timestamp>.md)"
    )
    return parser.parse_args()


def run_single_benchmark(
    client: httpx.Client,
    base_url: str,
    session_id: str,
    query: str,
    top_k: int,
    candidate_k: int,
) -> dict:
    payload = {
        "query": query,
        "session_id": session_id,
        "top_k": top_k,
        "candidate_k": candidate_k,
    }

    timings = None
    token_count = 0
    client_ttft = None
    error_msg = None

    t_client_start = time.perf_counter()
    first_token_seen = False

    try:
        with client.stream(
            "POST",
            f"{base_url}/benchmark/",
            json=payload,
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            buffer = ""

            for raw_chunk in response.iter_text():
                buffer += raw_chunk

                while "\n\n" in buffer:
                    message, buffer = buffer.split("\n\n", 1)

                    for line in message.strip().split("\n"):
                        if not line.startswith("data: "):
                            continue

                        data = json.loads(line[6:])

                        if data.get("type") == "token":
                            if not first_token_seen:
                                client_ttft = _elapsed_ms(t_client_start)
                                first_token_seen = True
                            token_count += 1

                        elif data.get("type") == "timings":
                            timings = data.get("timings", {})
                            token_count = data.get("token_count", token_count)

                        elif data.get("type") == "error":
                            error_msg = data.get("message", "Unknown error")

    except httpx.HTTPStatusError as exc:
        error_msg = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
    except httpx.ConnectError:
        error_msg = f"Cannot connect to {base_url}. Is the backend running?"
    except Exception as exc:
        error_msg = str(exc)

    client_total = _elapsed_ms(t_client_start)

    if error_msg:
        return {"error": error_msg}

    if timings is None:
        return {"error": "No timings event received from server."}

    # Merge client-side measurements
    timings["client_total_ms"] = round(client_total, 2)
    timings["client_ttft_ms"] = round(client_ttft, 2) if client_ttft else None
    timings["token_count"] = token_count

    return timings


def run_benchmark_suite(args) -> dict:
    client = httpx.Client()
    results = {"cold": [], "warm": [], "metadata": {}}

    results["metadata"] = {
        "query": args.query,
        "session_id": args.session_id,
        "top_k": args.top_k,
        "candidate_k": args.candidate_k,
        "base_url": args.base_url,
        "timestamp": datetime.now().isoformat(),
        "cold_runs": args.cold_runs,
        "warm_runs": args.warm_runs,
    }

    # ── Connectivity check ────────────────────────────────────────
    print("🔍 Checking backend connectivity...")
    try:
        resp = client.get(f"{args.base_url}/", timeout=5.0)
        resp.raise_for_status()
        print(f"  Backend is up: {resp.json()}\n")
    except Exception as exc:
        print(f"  Cannot reach backend at {args.base_url}: {exc}")
        sys.exit(1)

    # ── Cold runs ─────────────────────────────────────────────────
    print(f"❄️  Running {args.cold_runs} COLD request(s)...")
    print("   (First request may include model/embedding initialization)\n")

    for i in range(args.cold_runs):
        print(f"   Run {i + 1}/{args.cold_runs} ", end="", flush=True)
        result = run_single_benchmark(
            client=client,
            base_url=args.base_url,
            session_id=args.session_id,
            query=args.query,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
        )

        if "error" in result:
            print(f"❌ {result['error']}")
            results["cold"].append(result)
        else:
            total = result.get("client_total_ms", 0)
            ttft = result.get("ttft_ms", 0)
            print(f" total={total:.0f}ms  ttft={ttft:.0f}ms  tokens={result.get('token_count', 0)}")
            results["cold"].append(result)

        # Small delay between cold runs to simulate realistic spacing
        if i < args.cold_runs - 1:
            time.sleep(1.0)

    print()

    # ── Warm runs ─────────────────────────────────────────────────
    print(f"🔥 Running {args.warm_runs} WARM request(s)...")
    print("   (Caches are hot: embedding model, reranker, Gemini client loaded)\n")

    for i in range(args.warm_runs):
        print(f"   Run {i + 1}/{args.warm_runs} ", end="", flush=True)
        result = run_single_benchmark(
            client=client,
            base_url=args.base_url,
            session_id=args.session_id,
            query=args.query,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
        )

        if "error" in result:
            print(f"❌ {result['error']}")
            results["warm"].append(result)
        else:
            total = result.get("client_total_ms", 0)
            ttft = result.get("ttft_ms", 0)
            print(f"✅ total={total:.0f}ms  ttft={ttft:.0f}ms  tokens={result.get('token_count', 0)}")
            results["warm"].append(result)

        # Minimal delay between warm runs
        if i < args.warm_runs - 1:
            time.sleep(0.5)

    client.close()
    return results


def aggregate_stats(runs: list[dict], metric: str) -> dict | None:
    """Compute min/max/mean/median/p95 for a metric across successful runs."""
    values = [
        r[metric] for r in runs
        if "error" not in r and r.get(metric) is not None
    ]
    if not values:
        return None

    values_sorted = sorted(values)
    p95_idx = max(0, int(len(values_sorted) * 0.95) - 1)

    return {
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "p95": round(values_sorted[p95_idx], 2),
        "count": len(values),
    }


METRICS_OF_INTEREST = [
    ("total_ms",        "Total Latency (server)"),
    ("client_total_ms", "Total Latency (client)"),
    ("retrieval_ms",    "Retrieval (dense + BM25 + RRF)"),
    ("reranking_ms",    "Reranking (CrossEncoder + selection)"),
    ("prompt_build_ms", "Prompt Building"),
    ("ttft_ms",         "Time to First Token (server)"),
    ("client_ttft_ms",  "Time to First Token (client)"),
    ("generation_ms",   "Generation Duration"),
    ("gemini_total_ms", "Gemini Total (request → last token)"),
    ("guardrail_ms",    "Guardrail Validation"),
]


def generate_report(results: dict) -> str:
    meta = results["metadata"]
    lines = []

    lines.append("# FinLens RAG Pipeline — Latency Benchmark Report")
    lines.append("")
    lines.append(f"**Date:** {meta['timestamp']}")
    lines.append(f"**Query:** `{meta['query']}`")
    lines.append(f"**Config:** top_k={meta['top_k']}, candidate_k={meta['candidate_k']}")
    lines.append(f"**Runs:** {meta['cold_runs']} cold + {meta['warm_runs']} warm")
    lines.append("")

    # ── Summary table ─────────────────────────────────────────────
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Cold Mean (ms) | Warm Mean (ms) | Cold P95 (ms) | Warm P95 (ms) |")
    lines.append("|--------|---------------|---------------|--------------|--------------|")

    for metric_key, metric_label in METRICS_OF_INTEREST:
        cold_stats = aggregate_stats(results["cold"], metric_key)
        warm_stats = aggregate_stats(results["warm"], metric_key)

        cold_mean = f"{cold_stats['mean']:.1f}" if cold_stats else "—"
        warm_mean = f"{warm_stats['mean']:.1f}" if warm_stats else "—"
        cold_p95 = f"{cold_stats['p95']:.1f}" if cold_stats else "—"
        warm_p95 = f"{warm_stats['p95']:.1f}" if warm_stats else "—"

        lines.append(f"| {metric_label} | {cold_mean} | {warm_mean} | {cold_p95} | {warm_p95} |")

    lines.append("")

    # ── Key findings ──────────────────────────────────────────────
    cold_total = aggregate_stats(results["cold"], "total_ms")
    warm_total = aggregate_stats(results["warm"], "total_ms")
    cold_ttft = aggregate_stats(results["cold"], "ttft_ms")
    warm_ttft = aggregate_stats(results["warm"], "ttft_ms")
    cold_retrieval = aggregate_stats(results["cold"], "retrieval_ms")
    warm_retrieval = aggregate_stats(results["warm"], "retrieval_ms")
    cold_reranking = aggregate_stats(results["cold"], "reranking_ms")
    warm_reranking = aggregate_stats(results["warm"], "reranking_ms")

    lines.append("## Key Findings")
    lines.append("")

    if cold_total and warm_total:
        speedup = cold_total["mean"] / warm_total["mean"] if warm_total["mean"] > 0 else 0
        lines.append(f"- **Cold start total:** ~{cold_total['mean']:.0f}ms (mean)")
        lines.append(f"- **Warm request total:** ~{warm_total['mean']:.0f}ms (mean)")
        lines.append(f"- **Cold/warm ratio:** {speedup:.1f}x slower on first requests")

    if cold_ttft and warm_ttft:
        lines.append(f"- **Cold TTFT:** ~{cold_ttft['mean']:.0f}ms")
        lines.append(f"- **Warm TTFT:** ~{warm_ttft['mean']:.0f}ms")

    if cold_retrieval and warm_retrieval:
        lines.append(f"- **Retrieval:** cold ~{cold_retrieval['mean']:.0f}ms → warm ~{warm_retrieval['mean']:.0f}ms")

    if cold_reranking and warm_reranking:
        lines.append(f"- **Reranking:** cold ~{cold_reranking['mean']:.0f}ms → warm ~{warm_reranking['mean']:.0f}ms")

    lines.append("")

    # ── Per-stage breakdown ───────────────────────────────────────
    lines.append("## Pipeline Stage Breakdown")
    lines.append("")

    for phase_label, phase_key in [("Cold Requests", "cold"), ("Warm Requests", "warm")]:
        lines.append(f"### {phase_label}")
        lines.append("")

        if not results[phase_key]:
            lines.append("No successful runs.")
            lines.append("")
            continue

        lines.append("```")
        lines.append("Request Received")

        # Build the waterfall
        stage_metrics = [
            ("guardrail_ms",    "Guardrail check"),
            ("retrieval_ms",    "Hybrid retrieval"),
            ("reranking_ms",    "Reranking"),
            ("prompt_build_ms", "Prompt building"),
            ("ttft_ms",         "→ Time to first token"),
            ("generation_ms",   "→ Generation streaming"),
        ]

        for metric_key, stage_name in stage_metrics:
            stats = aggregate_stats(results[phase_key], metric_key)
            if stats:
                lines.append(f"      │")
                lines.append(f"      ├─ {stage_name}: {stats['mean']:.1f}ms")

        total_stats = aggregate_stats(results[phase_key], "total_ms")
        if total_stats:
            lines.append(f"      │")
            lines.append(f"      └─ Total: {total_stats['mean']:.1f}ms")

        lines.append("```")
        lines.append("")

    # ── Raw data ──────────────────────────────────────────────────
    lines.append("## Raw Measurements")
    lines.append("")

    for phase_label, phase_key in [("Cold", "cold"), ("Warm", "warm")]:
        lines.append(f"### {phase_label} Runs")
        lines.append("")

        successful = [r for r in results[phase_key] if "error" not in r]
        failed = [r for r in results[phase_key] if "error" in r]

        if successful:
            # Table header
            headers = ["Run", "Total", "Retrieval", "Rerank", "TTFT", "Generation", "Tokens"]
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

            for i, r in enumerate(successful, 1):
                row = [
                    str(i),
                    f"{r.get('total_ms', 0):.0f}ms",
                    f"{r.get('retrieval_ms', 0):.0f}ms",
                    f"{r.get('reranking_ms', 0):.0f}ms",
                    f"{r.get('ttft_ms', 0):.0f}ms",
                    f"{r.get('generation_ms', 0):.0f}ms",
                    str(r.get('token_count', 0)),
                ]
                lines.append("| " + " | ".join(row) + " |")

        if failed:
            lines.append("")
            lines.append(f"**{len(failed)} failed run(s):**")
            for r in failed:
                lines.append(f"- {r.get('error', 'Unknown')}")

        lines.append("")

    return "\n".join(lines)


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def main():
    args = parse_args()

    print("=" * 60)
    print("  FinLens RAG Pipeline — Latency Benchmark")
    print("=" * 60)
    print(f"  Backend:      {args.base_url}")
    print(f"  Session:      {args.session_id}")
    print(f"  Query:        {args.query}")
    print(f"  Cold runs:    {args.cold_runs}")
    print(f"  Warm runs:    {args.warm_runs}")
    print("=" * 60)
    print()

    results = run_benchmark_suite(args)

    # Generate and save report
    report = generate_report(results)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"latency_report_{timestamp}.md")

    output_path.write_text(report, encoding="utf-8")

    print()
    print("=" * 60)
    print(f"   Report saved to: {output_path.resolve()}")
    print("=" * 60)
    print()

    # Also print the summary to stdout
    print(report)

    # Save raw JSON data alongside the report
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n📦 Raw data saved to: {json_path.resolve()}")


if __name__ == "__main__":
    main()
