# SSH & Deployment Commands

## 1. Fix Key Permissions (Windows PowerShell)

Run if receiving `UNPROTECTED PRIVATE KEY FILE!` errors:

```powershell
# Reset inheritance and grant read access only to current user
icacls .\techgenz.pem /reset
icacls .\techgenz.pem /grant:r "$($env:USERNAME):(R)"
icacls .\techgenz.pem /inheritance:r
```

---

## 2. Connect via SSH

```powershell
ssh -i "techgenz.pem" linux1@148.100.77.254
# Or if configured in ~/.ssh/config:
# ssh ibm-linuxone
```

### Verify IBM Z / s390x Architecture
```bash
uname -m
cat /proc/cpuinfo | grep -E "machine|cpu"
```

---

## 3. Copy Code to Remote (Local PowerShell)

```powershell
# Ensure destination exists
ssh ibm-linuxone "mkdir -p ~/LUCID-Z"

# Sync files
scp -r app docs output sample-dataset *.py *.md requirements.txt ibm-linuxone:~/LUCID-Z/
```

---

## 4. Setup & Run (Remote Terminal)

```bash
cd ~/LUCID-Z

# System dependencies
sudo apt update && sudo apt install -y tshark

# Virtual environment & packages
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access dashboard at: **http://148.100.77.254:8000**

---

## 5. Applying Changes (When & What to Run)

Run these commands from your **local Windows PowerShell** whenever you edit code locally and want to reflect changes on the server.

### Scenario A: You only modified Python code or dashboard files (`app/` folder)
*Use this when updating `app/main.py`, templates (`.html`), styling (`.css`), or JavaScript.*

**Step 1 — Upload modified app files:**
```powershell
scp -r app ibm-linuxone:~/LUCID-Z/
```

**Step 2 — Restart the server on the mainframe:**
```powershell
ssh ibm-linuxone "pkill -f uvicorn; cd ~/LUCID-Z && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/app.log 2>&1 &"
```

**Step 3 — Check if server is running:**
```powershell
ssh ibm-linuxone "pgrep -fa uvicorn"
```
*(If running, it outputs the process ID and command line, e.g., `27822 python3 -m uvicorn ...`)*

**Step 4 — View latest logs or stream them live:**
```powershell
# View the last 20 lines of logs
ssh ibm-linuxone "tail -n 20 ~/app.log"

# Or follow/stream logs in real time (Press Ctrl+C to stop)
ssh ibm-linuxone "tail -f ~/app.log"
```

---

### Scenario B: You modified datasets, models, or root Python scripts
*Use this when changing `output/*.h5`, `sample-dataset/`, `lucid_cnn.py`, `lucid_dataset_parser.py`, or documentation.*

**Step 1 — Upload all modified directories:**
```powershell
scp -r app docs output sample-dataset *.py *.md ibm-linuxone:~/LUCID-Z/
```

**Step 2 — Restart the server on the mainframe:**
```powershell
ssh ibm-linuxone "pkill -f uvicorn; cd ~/LUCID-Z && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/app.log 2>&1 &"
```

---

### Scenario C: You added new system or Python packages
*Use this if new libraries are added to `requirements.txt`.*

**Step 1 — Upload requirements file:**
```powershell
scp requirements.txt ibm-linuxone:~/LUCID-Z/
```

**Step 2 — Install package on server and restart:**
```powershell
ssh ibm-linuxone "pip install --break-system-packages -r ~/LUCID-Z/requirements.txt"
ssh ibm-linuxone "pkill -f uvicorn; cd ~/LUCID-Z && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/app.log 2>&1 &"
```

---

## 6. Accessing the Dashboard

After running the steps above, refresh your browser:
👉 **`http://148.100.77.254:8000`**

