# LUCID-Z: System Summary, Pipeline & Execution Guide

## 1. Overview & Purpose

**LUCID-Z** (adapted from *LUCID: A Practical, Lightweight Deep Learning Solution for DDoS Attack Detection*) is an online, real-time DDoS detection and traffic monitoring system enhanced for the **IBM Z Datathon 2026** (*AI for Good: Real-Time AI for Critical Decisions*).

Traditional batch security systems react after attacks have already saturated networks and damaged services. LUCID-Z evaluates bidirectional traffic flows in real-time time-windows (e.g., 10 seconds), classifies each flow as **Benign** or **DDoS** using a compact Convolutional Neural Network (CNN), and serves live statistics, risk scores, hysteresis-controlled alerts, and mitigation controls via a web dashboard.

### Core Objectives
- **Sub-Second DDoS Detection**: Fast detection within 10-second windows with microsecond-level model inference.
- **Transactional AI for IBM Z**: Enables low-latency scoring on enterprise mainframes where transaction data lives (via IBM Machine Learning for z/OS or running natively on LinuxONE `s390x`).
- **Explainability & Active Mitigation**: Identifies top offending IPs, attacked ports, attack probability, and generates one-click mitigation rules (`iptables` / ACL rules).

---

## 2. Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Language & Environment** | Python 3.9 – 3.11, Docker (x86_64 and IBM LinuxONE `s390x`) |
| **Deep Learning & ML** | TensorFlow 2.7.1, Keras, scikit-learn, NumPy, h5py |
| **Packet Capture & Parsing** | Pyshark (0.6), Wireshark/tshark (3.2.3 or 3.6+), Npcap (on Windows) |
| **Web Backend** | FastAPI (0.115), Uvicorn (standard), AnyIO, WebSockets |
| **Frontend** | Vanilla HTML5 / Modern CSS / JavaScript, Real-time WebSocket stream |
| **Mainframe Integrations** | IBM Machine Learning for z/OS REST client (`app/ibmzml.py`), hardware environment detector (`app/ibmz.py`) |

---

## 3. End-to-End Pipeline

```
┌────────────────────────────────────────────────────────┐
│  Traffic Source (Live Interface / PCAP / HTTP Ingest)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  1. Packet Capture & Flow Aggregation (Pyshark/tshark) │
│     - Groups packets into 5-tuple bidirectional flows  │
│       (srcIP, srcPort, dstIP, dstPort, protocol)       │
│     - Splits flows across time window 't' (e.g., 10s)  │
│     - Captures up to 'n' packets per flow (e.g., 10)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  2. Feature Extraction & Preprocessing (util_functions)│
│     - Extracts 11 features per packet                  │
│       (sizes, intervals, TCP flags, header lengths)    │
│     - Normalizes features via Min-Max scaling [0, 1]   │
│     - Zero-pads matrices to fixed input shape (n x 11) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  3. Model Scoring & Inference                          │
│     Dual-Engine Strategy with automatic fallback:      │
│     ├── Option A: IBM ML for z/OS (Microsecond REST)   │
│     └── Option B: Local TensorFlow Keras Model (.h5)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  4. Alerting & Risk Engine                             │
│     - Evaluates DDoS window probability                │
│     - Applies Hysteresis to prevent alert flapping     │
│     - Calculates real-time metrics (TPR, FPR, TTD)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  5. Real-Time WebSocket Broadcast & Dashboard          │
│     - Live stream updates to browser UI (/api/stream)  │
│     - Attack timeline, target ports, and top source IPs│
│     - Auto-generated iptables / firewall rules         │
└────────────────────────────────────────────────────────┘
```

---

## 4. Repository Structure

- `app/`
  - `main.py`: FastAPI backend, background workers, WebSocket broadcasting, and REST endpoints.
  - `ibmzml.py`: REST scoring client for IBM ML for z/OS.
  - `ibmz.py`: Runtime architecture inspector (identifies `s390x`, z13–z16, and Telum coprocessor).
  - `templates/` & `static/`: Real-time monitoring dashboard and UI styling.
- `lucid_cnn.py`: Defines the CNN model, training routine, callbacks, and grid search hyperparameter tuning.
- `lucid_dataset_parser.py`: PCAP extraction, bidirectional flow generator, and HDF5 dataset builder.
- `util_functions.py`: Data normalization, feature scaling, and zero-padding utilities.
- `sample-dataset/`: Sample PCAP traces (CIC-DDoS2019) for immediate local testing.
- `output/`: Pre-trained models (e.g. `10t-10n-DOS2019-LUCID.h5`).

---

## 5. How to Run the Code

### 5.1 Prerequisites

1. **Python**: Python 3.9 (recommended) or 3.10.
2. **Wireshark & TShark**:
   - **Windows**: Install [Wireshark](https://www.wireshark.org/) with Npcap and TShark. Add `C:\Program Files\Wireshark` to your `PATH`.
   - **Linux / Ubuntu**:
     ```bash
     sudo apt update && sudo apt install -y tshark
     ```

### 5.2 Environment Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 2. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 5.3 Running the Real-Time Web Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Open **http://127.0.0.1:8000** in your browser.
- **Select Source**:
  - **PCAP File Playback**: Choose a sample PCAP file from `sample-dataset/` (e.g., `sample-dataset/CIC-DDoS2019-sample.pcap`).
  - **Live Network Interface**: Select your network interface (`Ethernet`, `Wi-Fi`, or Npcap device).
- **Select Model**: Choose `output/10t-10n-DOS2019-LUCID.h5`.
- Click **Start** to monitor live classification, alerts, and mitigation recommendations.

---

### 5.4 Running Data Preprocessing (PCAP to Dataset)

To extract features from raw `.pcap` files:

```bash
# Step 1: Parse PCAPs into intermediate flow representations (.data)
python lucid_dataset_parser.py --dataset_type DOS2019 --dataset_folder ./sample-dataset/ --packets_per_flow 10 --dataset_id DOS2019 --traffic_type all --time_window 10

# Step 2: Balance, normalize, pad, and split into HDF5 training/val/test sets
python lucid_dataset_parser.py --preprocess_folder ./sample-dataset/
```

---

### 5.5 Training the CNN Model

To train the CNN model over preprocessed HDF5 files:

```bash
python lucid_cnn.py --train ./sample-dataset/ --epochs 50
```
The best model checkpoint based on validation loss will be automatically saved under `./output/` with format `<t>t-<n>n-<dataset>-LUCID.h5`.

---

### 5.6 Running via Docker (Container / LinuxONE)

```bash
# Build the container image
docker build -t lucid-z .

# Run the container (optionally pass IBM ML for z/OS credentials)
docker run -p 8000:8000 \
  -e IBMZML_SCORING_URL=https://<zos-host>:<port>/v1/model/<model-id>/predict \
  -e IBMZML_TOKEN=<jwt-token> \
  lucid-z
```
