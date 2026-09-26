# FinLens RAG Pipeline — Latency Benchmark Report

**Date:** 2026-09-26T21:08:52.611058
**Query:** `What were the total revenues reported?`
**Config:** top_k=6, candidate_k=20
**Runs:** 5 cold + 5 warm

## Summary

| Metric | Cold Mean (ms) | Warm Mean (ms) | Cold P95 (ms) | Warm P95 (ms) |
|--------|---------------|---------------|--------------|--------------|
| Total Latency (server) | 7718.3 | 3125.4 | 3514.2 | 3114.0 |
| Total Latency (client) | 7724.6 | 3126.7 | 3516.0 | 3115.0 |
| Retrieval (dense + BM25 + RRF) | 1745.5 | 23.0 | 83.4 | 25.0 |
| Reranking (CrossEncoder + selection) | 1653.4 | 360.2 | 384.2 | 368.6 |
| Prompt Building | 0.1 | 0.0 | 0.1 | 0.1 |
| Time to First Token (server) | 3296.2 | 1636.6 | 2124.2 | 1806.6 |
| Time to First Token (client) | 6709.5 | 2025.5 | 2515.9 | 2194.2 |
| Generation Duration | 1015.9 | 1101.0 | 1007.1 | 1230.8 |
| Gemini Total (request → last token) | 4312.2 | 2737.7 | 3124.1 | 2717.9 |
| Guardrail Validation | 0.2 | 0.0 | 0.1 | 0.0 |

## Key Findings

- **Cold start total:** ~7718ms (mean)
- **Warm request total:** ~3125ms (mean)
- **Cold/warm ratio:** 2.5x slower on first requests
- **Cold TTFT:** ~3296ms
- **Warm TTFT:** ~1637ms
- **Retrieval:** cold ~1746ms → warm ~23ms
- **Reranking:** cold ~1653ms → warm ~360ms

## Pipeline Stage Breakdown

### Cold Requests

```
Request Received
      │
      ├─ Guardrail check: 0.2ms
      │
      ├─ Hybrid retrieval: 1745.5ms
      │
      ├─ Reranking: 1653.4ms
      │
      ├─ Prompt building: 0.1ms
      │
      ├─ → Time to first token: 3296.2ms
      │
      ├─ → Generation streaming: 1015.9ms
      │
      └─ Total: 7718.3ms
```

### Warm Requests

```
Request Received
      │
      ├─ Guardrail check: 0.0ms
      │
      ├─ Hybrid retrieval: 23.0ms
      │
      ├─ Reranking: 360.2ms
      │
      ├─ Prompt building: 0.0ms
      │
      ├─ → Time to first token: 1636.6ms
      │
      ├─ → Generation streaming: 1101.0ms
      │
      └─ Total: 3125.4ms
```

## Raw Measurements

### Cold Runs

| Run | Total | Retrieval | Rerank | TTFT | Generation | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 26725ms | 8556ms | 7022ms | 9990ms | 1152ms | 7 |
| 2 | 2974ms | 83ms | 384ms | 1507ms | 986ms | 6 |
| 3 | 2502ms | 27ms | 260ms | 1274ms | 934ms | 6 |
| 4 | 3514ms | 39ms | 345ms | 2124ms | 1000ms | 6 |
| 5 | 2876ms | 22ms | 256ms | 1586ms | 1007ms | 6 |

### Warm Runs

| Run | Total | Retrieval | Rerank | TTFT | Generation | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 3499ms | 19ms | 337ms | 2212ms | 928ms | 6 |
| 2 | 3089ms | 26ms | 353ms | 1807ms | 897ms | 6 |
| 3 | 3114ms | 24ms | 369ms | 1373ms | 1345ms | 7 |
| 4 | 3028ms | 22ms | 332ms | 1566ms | 1104ms | 7 |
| 5 | 2896ms | 25ms | 411ms | 1225ms | 1231ms | 7 |
