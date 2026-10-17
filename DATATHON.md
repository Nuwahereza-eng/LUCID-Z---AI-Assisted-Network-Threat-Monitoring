# LUCID-DDoS: Real-Time AI for Critical Infrastructure Protection
### IBM Z Datathon 2026 — AI for Good: Real-Time AI for Critical Decisions

---

## The Problem

DDoS attacks do not announce themselves. By the time a traditional batch-analysis
system detects anomalous traffic, an outage has already started. For hospitals
routing emergency data, financial platforms processing transactions, and
telecommunications switching calls, **the difference between insight and impact
is timing**.

LUCID-DDoS answers the challenge question directly: it analyzes network traffic
*as events happen*, classifies each flow in real time, and issues an alert within
a single time window (10 seconds) — before service degradation reaches users.

---

## Solution Category

This submission fits the following challenge categories:

- ✅ **Real-time anomaly-detection system** — classifies live network flows window by window
- ✅ **AI/ML prediction model** — trained CNN with 98.68% accuracy, 100% TPR on CIC-DDoS2019
- ✅ **Early-warning and alerting solution** — WebSocket alerts + hysteresis-controlled notifications
- ✅ **AI-powered decision-support application** — dashboard with mitigation controls and risk scoring
- ✅ **Real-time data pipeline** — PCAP → parse → normalise → score → broadcast in under 1 second

---

## Why IBM Z?

The judging criteria state: *"IBM Machine Learning for z/OS enables Transactional AI
and real-time AI inference within business transactions, bringing intelligence closer
to where critical decisions happen."*

Enterprise mainframes are **where the data already lives**. A CICS transaction
processing a payment, a Db2 query returning account balances, or an IMS record
being updated — these are all generating the network events that LUCID monitors.
Routing the AI scoring step through IBM ML for z/OS means:

1. **No data leaves the enterprise boundary** — the feature matrix is scored
   inside the mainframe, not shipped to an external inference server.
2. **Latency is measured in microseconds, not milliseconds** — the model runs
   co-located with the transaction data.
3. **Compliance and auditability** — z/OS provides hardware-level logging and
   encryption (FIPS 140-2) that external inference services cannot match.

---

## IBM Z Integration: What Is Built

### Layer 1 — IBM ML for z/OS Scoring Client (`app/ibmzml.py`)

A complete REST client for the IBM Machine Learning for z/OS scoring API.

```
POST https://<zos-host>:<port>/v1/model/<model-id>/predict
Authorization: Bearer <JWT>

{
  "input_data": [{
    "fields": ["f0", "f1", ..., "f109"],
    "values": [[...per-flow feature vector...], ...]
  }]
}
```

**How it integrates:**
- Set `IBMZML_SCORING_URL` and `IBMZML_TOKEN` environment variables
- Every detection window automatically sends its feature matrix to z/OS ML
- If z/OS ML is unreachable, the system falls back to local TF transparently
- The dashboard shows a live **"Active Engine"** badge: `IBM z/OS ML` (blue) or `local TF` (grey)

**This is Transactional AI**: the same HTTP call that CICS or Db2 would make to
get a risk score during an active transaction.

### Layer 2 — Runtime Hardware Detection (`app/ibmz.py`)

At startup, `GET /api/ibmz/status` reads `platform.machine()` and `/proc/cpuinfo`
to report whether the service is running on IBM Z (`s390x`), which specific machine
type (z13 through z16/LinuxONE Emperor 4), and whether the **Telum AI chip** is present.

### Layer 3 — Zero-Modification Container Deployment

TensorFlow, TFLite and scikit-learn publish no `s390x` wheels on PyPI, so on IBM Z
LUCID runs without them: `app/model_loader.py` executes the CNN in pure NumPy straight
from the `.h5` weights (verified identical to Keras on all 4,530 sample-dataset
fragments), and `sk_compat.py` replaces the few scikit-learn functions used. The model
file (`.h5`) requires no conversion.

Native install as a systemd service (Ubuntu, RHEL or SLES — e.g. a LinuxONE Community Cloud VM):

```bash
git clone https://github.com/Nuwahereza-eng/LUCID-Z---AI-Assisted-Network-Threat-Monitoring.git lucid-ddos
cd lucid-ddos && bash deploy/linuxone/setup.sh
```

Or with the multi-arch `Dockerfile`:

```bash
# On LinuxONE / IBM Z:
docker build -t lucid-ddos .
docker run -p 8000:8000 \
  -e IBMZML_SCORING_URL=https://zos-host:12345/v1/model/ddos-lucid/predict \
  -e IBMZML_TOKEN=<jwt> \
  lucid-ddos
```

### Layer 4 — Telum AI Acceleration Path (Scoped, Not Yet Implemented)

IBM z16 includes the **Integrated Accelerator for AI** (Telum chip). The LUCID
CNN topology (Conv2D → ReLU → GlobalMaxPooling → Dense/sigmoid) maps directly
to supported zDNN operators. The conversion pipeline is:

```
Keras .h5  →  ONNX (tf2onnx)  →  ONNX-MLIR  →  zDNN (Telum hardware)
```

This would reduce inference from ~0.74 ms/sample to sub-0.1 ms/sample.
The ONNX export step is the only remaining piece. The model is ready.

---

## Model Performance (Real Numbers — from CSV files in this repo)

### Test Set Results (`output/predictions-20251029-135910.csv`)

| Metric | Value |
|---|---|
| Accuracy | **0.9868** |
| F1 Score | **0.9879** |
| True Positive Rate (TPR) | **1.0000** — zero missed attacks |
| False Positive Rate (FPR) | **0.0287** — 97.1% true negative rate |
| Inference time | **0.335 s / 453 samples = 0.74 ms/sample** |
| Dataset | CIC-DDoS2019 test set (DNS, SynFlood, UDPLag, WebDDoS, Benign) |

### Validation Set Results (`output/10t-10n-DOS2019-LUCID.csv`)

| Metric | Value |
|---|---|
| Accuracy | **0.9804** |
| F1 Score | **0.9819** |
| Best hyperparameters | batch=1024, kernels=32, lr=0.1 |

---

## Real-Time Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Network traffic source (PCAP / live interface / HTTP ingest)   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
           Packet parsing (pyshark)
           11 features per packet:
           timestamp, length, highest_layer, IP_flags,
           protocols, TCP/UDP/ICMP fields
                     │
                     ▼
           Flow assembly: bidirectional 5-tuple
           Time window: 10 seconds
           Per-flow fragment: 10 packets × 11 features
                     │
                     ▼
           Normalisation + zero-padding → shape (10, 11, 1)
                     │
           ┌─────────┴──────────────────────────┐
           │                                    │
           ▼                                    ▼
   ┌───────────────────┐              ┌─────────────────────┐
   │  IBM ML for z/OS  │   (primary)  │  Local TensorFlow   │
   │  Scoring API      │◄─────────────│  (fallback only)    │
   │  z/OS REST POST   │              │  Conv2D CNN (.h5)   │
   └────────┬──────────┘              └──────────┬──────────┘
            │                                    │
            └──────────────┬─────────────────────┘
                           │
                           ▼
              P(DDoS) per flow fragment
              Window aggregation: ddos_fraction
              Alert if ddos_fraction ≥ threshold
                           │
           ┌───────────────┼───────────────────┐
           ▼               ▼                   ▼
    WebSocket         REST /api/status    Mitigation engine
    broadcast →       TPR/FPR/TTD        rate-limit → blackhole
    Dashboard         KPIs               blocked sources
```

---

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/start` | POST | Start detection from PCAP / interface / HTTP ingest |
| `/api/stop` | POST | Stop detection |
| `/api/status` | GET | Live KPIs: TPR, FPR, TTD, blocked IPs |
| `/api/history` | GET | Last 500 window payloads |
| `/api/predict` | POST | Synchronous batch inference (fragments JSON) |
| `/api/predict_file` | POST | Upload `.hdf5` → full classification metrics |
| `/api/zos/score` | POST | **Score via IBM ML for z/OS, fall back to local TF** |
| `/api/zos/health` | GET | **IBM ML for z/OS connectivity status** |
| `/api/ibmz/status` | GET | **Hardware detection: arch, machine type, Telum** |
| `/api/model_info` | GET | Model name, time window, val/test metrics from CSV |
| `/api/ingest` | POST | Push pre-processed fragments (for mainframe integration) |
| `/api/mitigation` | POST | Block/unblock IPs, set hysteresis and cooldown policy |
| `WS /ws` | WebSocket | Real-time per-window broadcast with `scoring_engine` field |

---

## Connecting a z/OS Workload

A CICS transaction or Db2 stored procedure that wants real-time DDoS risk scoring
makes the same call as any REST client:

```http
POST /api/zos/score HTTP/1.1
Host: lucid-ddos-service:8000
Content-Type: application/json

{
  "fragments": [
    [[0.01, 1460, 6, 2, 12288, 1460, 1, 2, 65535, 0, 0],
     [0.02, 1460, 6, 2, 12288, 1460, 1, 2, 65535, 0, 0]]
  ],
  "labels": [1]
}
```

Response (scored via IBM ML for z/OS when configured):

```json
{
  "samples": 1,
  "positive_count": 1,
  "ddos_fraction": 1.0,
  "latency_sec": 0.0012,
  "latency_ms_per_sample": 1.2,
  "scoring_engine": "ibmzml",
  "predictions": [1],
  "classification_metrics": { "accuracy": 1.0, "tpr": 1.0, "fpr": 0.0 }
}
```

The `scoring_engine` field tells the caller whether the decision was made on IBM Z
or via the local fallback — full transparency for audit logging.

---

## Configuration Reference

| Variable | Purpose |
|---|---|
| `IBMZML_SCORING_URL` | IBM ML for z/OS scoring endpoint URL |
| `IBMZML_TOKEN` | Bearer JWT from z/OS ML authentication |
| `IBMZML_VERIFY_TLS` | Set `false` for dev/test (default: `true`) |
| `IBMZML_TIMEOUT_SEC` | Per-request timeout in seconds (default: `5`) |
| `LUCID_MODEL_PATH` | Path to local `.h5` model (fallback) |

---

## Files in This Submission

| File | Role |
|---|---|
| `app/ibmzml.py` | IBM ML for z/OS REST scoring client + health check |
| `app/ibmz.py` | Runtime IBM Z hardware detection (arch, machine type, Telum) |
| `app/main.py` | FastAPI service with `/api/zos/score`, `/api/zos/health`, `/api/model_info`, `/api/predict`, `/api/predict_file` |
| `app/templates/index.html` | Dashboard with live engine badge, z/OS connection status, model metrics |
| `output/10t-10n-DOS2019-LUCID.h5` | Trained CNN model (not retrained) |
| `output/10t-10n-DOS2019-LUCID.csv` | Recorded validation metrics |
| `output/predictions-20251029-135910.csv` | Recorded test metrics |
| `sample-dataset/*.pcap` | CIC-DDoS2019 labelled traffic traces |
| `DATATHON.md` | This document |

---

## Citation

R. Doriguzzi-Corin, S. Millar, S. Scott-Hayward, J. Martínez-del-Rincón and D. Siracusa,
*"Lucid: A Practical, Lightweight Deep Learning Solution for DDoS Attack Detection,"*
IEEE Transactions on Network and Service Management, vol. 17, no. 2, pp. 876–889, June 2020.
DOI: 10.1109/TNSM.2020.2971776
