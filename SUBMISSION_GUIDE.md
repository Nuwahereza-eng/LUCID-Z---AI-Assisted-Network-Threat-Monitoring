# IBM Z Datathon 2026 — Submission Guide (LUCID-DDoS)

Submission portal: hack2skill.com/event/datathon-2026 · Video guide: youtu.be/3_L3T__zEco
Closing ceremony: **18 Oct, 10:30 AM IST**. Submit early, not in the last minutes.



## 1. Pre-submission checklist

- [ ] Team of 4–6 members registered
- [ ] Event code **SSF2026** added to the project description, and to the top of the GitHub README
- [ ] GitHub repo is public: https://github.com/Nuwahereza-eng/LUCID-Z---AI-Assisted-Network-Threat-Monitoring (it is)
- [ ] No secrets in the repo: `ddos.pem`, `.env` and `.demo_token` are gitignored and not committed (checked)
- [ ] Screenshots of the LinuxONE instance saved (see §5); the deck says judges look for this evidence
- [ ] Pitch deck PDF named **`[Team Name]_IBM Z Datathon 2026 Project.pdf`**, under 5 MB
- [ ] Video uploaded to YouTube/Vimeo, **3 minutes or less**, 720p/1080p, set to *Public* or *Unlisted* (not Private)
- [ ] Every link opened in a private/incognito window to confirm it works without signing in

---

## 2. Form answers (copy and paste; each is under 1,024 characters)

### Challenges
Select: **Real-Time AI for Critical Decisions**

### What is the problem you are trying to solve?
```text
DDoS attacks can take hospitals, banks, payment systems and telecom networks offline within minutes. Many organisations still detect them with batch log analysis or fixed rate thresholds, so the alert arrives after users already feel the outage, and simple thresholds either miss low-rate attacks or flood operators with false alarms. Security teams need a detector that classifies traffic as it arrives, explains which sources are attacking, and is light enough to run next to the critical workloads it protects, including on enterprise platforms like IBM Z where much of this transactional data lives.
```

### How are you planning to solve the problem? (Brief Overview)
```text
LUCID-DDoS is a real-time detection pipeline and dashboard built on LUCID, an open-source lightweight CNN for DDoS detection (Doriguzzi-Corin et al., IEEE TNSM 2020, Apache-2.0). Traffic from a PCAP replay, a network interface or an HTTP feed is parsed with PyShark/tshark into 10-second windows. Each flow becomes a 10-packet x 11-feature matrix that the CNN scores. Windows whose attack fraction crosses a threshold raise alerts, which a FastAPI backend streams over WebSockets to a live dashboard showing risk trend, offending sources, mitigation suggestions and audible alerts. The model reaches 98.68% accuracy on held-out CIC-DDoS2019 test data. During the datathon we ported the system to IBM LinuxONE: TensorFlow has no s390x wheels, so we wrote a pure-NumPy inference engine that reads the trained Keras weights directly and gives identical results. We also added an IBM ML for z/OS scoring client, IBM Z hardware detection and a one-command LinuxONE deployment.
```

### How does your solution leverage IBM Z / LinuxONE technologies?
```text
LUCID-DDoS runs natively on an IBM LinuxONE Community Cloud VM (s390x, IBM z17, machine type 9175, Ubuntu 22.04) as a systemd service. Porting it meant solving real s390x problems: TensorFlow, TFLite and scikit-learn publish no s390x wheels, so we built a NumPy inference engine and validated it on big-endian IBM Z hardware, where it matches the original model exactly (98.68% test accuracy). On LinuxONE the service uses about 96 MB of RAM and scores a full PCAP replay in about 6 seconds. A detection endpoint reads the hardware and reports the z17 and its Telum II AI accelerator. Planned next steps (built but not yet connected): an IBM Machine Learning for z/OS REST scoring client that routes each detection window to a z/OS ML endpoint for Transactional AI, falling back to local inference automatically; and exporting the CNN to ONNX to run on Telum II through IBM zDNN. This keeps detection next to the transactional data it protects.
```

### What value does your solution deliver, and who will benefit from it?
```text
Beneficiaries are security operations teams at organisations running critical services: hospitals, banks and payment processors, telecom operators, ISPs, government and universities, especially those already running IBM Z or LinuxONE. The outcome is an alert within one 10-second traffic window instead of after an outage, a list of the sources responsible, and suggested mitigations, so operators can act before users are affected. Because the model is tiny (about 1,100 parameters) and the service needs only about 96 MB of RAM with no GPU or TensorFlow, it can run alongside existing workloads on the mainframe without new infrastructure, keeping sensitive traffic data inside the enterprise boundary. Business value: less downtime and lost revenue during attacks, fewer false alarms than fixed thresholds, and an open-source, auditable model that organisations can retrain on their own traffic.
```

### GitHub link
```text
https://github.com/Nuwahereza-eng/LUCID-Z---AI-Assisted-Network-Threat-Monitoring
```

### Link to all open-source resources used
```text
LUCID paper: https://doi.org/10.1109/TNSM.2020.2971776
CIC-DDoS2019 dataset (UNB): https://www.unb.ca/cic/datasets/ddos-2019.html
TensorFlow/Keras (training): https://github.com/tensorflow/tensorflow
NumPy: https://github.com/numpy/numpy
h5py: https://github.com/h5py/h5py
scikit-learn: https://github.com/scikit-learn/scikit-learn
PyShark: https://github.com/KimiNewt/pyshark
Wireshark/tshark: https://www.wireshark.org
FastAPI: https://github.com/fastapi/fastapi
Uvicorn: https://github.com/encode/uvicorn
Pydantic: https://github.com/pydantic/pydantic
LiteRT (TFLite runtime): https://github.com/google-ai-edge/LiteRT
Chart.js: https://github.com/chartjs/Chart.js
IBM Plex font: https://github.com/IBM/plex
```

### Video submission link
Your YouTube/Vimeo URL. Set it to Unlisted or Public, never Private.

### Pitch deck
Upload the PDF, or if it's over 5 MB, share a link that opens without requesting access.

### Other documents (optional, recommended)
An architecture diagram; see §4 for what it should show. Link it as a PDF/PNG in the repo or on a public share.

---

## 3. Demo video plan (3:00 max)

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | Title slide → news headline/stat on DDoS outages | The problem: DDoS hits critical services, and batch detection is too late |
| 0:25–0:50 | Architecture diagram | Pipeline: traffic → 10 s windows → CNN → alert → dashboard; built on open-source LUCID |
| 0:50–1:30 | **Terminal, one continuous take:** `ssh` into LinuxONE → `uname -m` (s390x) → `head /proc/sysinfo` (IBM, type 9175) → `lscpu \| grep "Byte Order"` (Big Endian) → `systemctl status lucid-ddos` | Proof it runs on IBM Z, and the s390x port (NumPy engine, identical accuracy) |
| 1:30–2:20 | Dashboard via the SSH tunnel: IBM Z status (z17 / Telum II) → run the **SynFlood** preset → alert fires, offending sources appear → run **Benign** → stays green | Real-time detection on LinuxONE; low false positives |
| 2:20–2:45 | Slide: results (98.68% accuracy, ~96 MB RAM, ~6 s replay on z17) | Value for SOC teams; runs beside mainframe workloads |
| 2:45–3:00 | Slide: next steps (z/OS ML scoring, Telum II via ONNX/zDNN) + team | Roadmap; thank you |

Keep the terminal and dashboard parts as one unedited recording. That's your strongest evidence that it really runs on their server.

---

## 4. Pitch deck outline (about 10 slides)

1. Title: team name, project name, *IBM Z Datathon 2026 · Real-Time AI for Critical Decisions*, SSF2026
2. Problem: DDoS impact on critical services; why batch detection fails
3. Solution: LUCID-DDoS in one sentence + dashboard screenshot
4. Architecture: Traffic (PCAP / interface / HTTP ingest) → PyShark parser → 10 s windows, 10×11 flow matrices → CNN (NumPy engine on s390x) → threshold and alerting → FastAPI + WebSocket → dashboard. Side box: *planned: IBM ML for z/OS scoring, Telum II via zDNN*
5. IBM Z / LinuxONE: s390x port story, z17 screenshot, big-endian validation
6. Live results: SynFlood detected; benign 2 false alarms out of 124 windows; 98.68% accuracy
7. Performance: ~96 MB RAM, ~6 s per PCAP replay on z17, ~1,100-parameter model
8. Value and beneficiaries
9. Roadmap and team

---

## 5. Screenshots to take on LinuxONE (save them now)

The server stopped answering SSH and ping at the end of this session. Check the VM is running in the Community Cloud dashboard (linuxone.cloud.marist.edu) before recording.

```bash
ssh -i ddos.pem -L 8000:127.0.0.1:8000 linux1@148.100.78.102
uname -a
head -20 /proc/sysinfo          # Manufacturer IBM, Type 9175
lscpu | grep -E "Architecture|Byte Order"
systemctl status lucid-ddos --no-pager
grep backend= ~/setup.log        # arch=s390x byteorder=big test_accuracy=0.9868
```
Then in the browser at http://localhost:8000: the dashboard, the IBM Z status (`/api/ibmz/status`), and a SynFlood detection in progress.

---

## 6. Claims to keep accurate

Judges may check these, so don't overstate:
- **z/OS ML** is *built but not connected*. You have no z/OS ML endpoint, so don't say detections are scored on z/OS.
- **Telum II** is *present on the hardware*, but LUCID does *not* use it yet.
- **98.68%** is the accuracy on the 453-sample CIC-DDoS2019 test split, not on live traffic.
- "Live interface capture" works locally but was not used on LinuxONE. Only PCAP replay ran there.
