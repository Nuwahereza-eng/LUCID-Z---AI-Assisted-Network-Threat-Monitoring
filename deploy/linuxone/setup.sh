#!/usr/bin/env bash
# Set up LUCID-DDoS on an IBM LinuxONE / IBM Z (s390x) Linux server and run it
# as a systemd service on port 8000. Works on Ubuntu/Debian, RHEL and SLES.
#
#   git clone https://github.com/Nuwahereza-eng/LUCID-Z---AI-Assisted-Network-Threat-Monitoring.git lucid-ddos
#   cd lucid-ddos && bash deploy/linuxone/setup.sh
#
# Private by default: the dashboard listens on 127.0.0.1 only and no firewall
# ports are opened. View it from your own machine through an SSH tunnel:
#   ssh -i key.pem -L 8000:127.0.0.1:8000 <user>@<server-ip>   then open http://localhost:8000
# PUBLIC=1 bash deploy/linuxone/setup.sh  exposes it on the server's IP (no login — use with care)
# Custom port:  PORT=8080 bash deploy/linuxone/setup.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT="${PORT:-8000}"
PUBLIC="${PUBLIC:-0}"
HOST=127.0.0.1; [ "$PUBLIC" = "1" ] && HOST=0.0.0.0
RUN_USER="$(id -un)"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "==> Architecture: $(uname -m)   App dir: $APP_DIR"
. /etc/os-release

echo "==> Installing system packages (tshark, Python, numpy/h5py where packaged)"
case "$ID $ID_LIKE" in
  *ubuntu*|*debian*)
    $SUDO apt-get update
    echo "wireshark-common wireshark-common/install-setuid boolean false" | $SUDO debconf-set-selections
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      tshark python3 python3-venv python3-pip python3-dev python3-numpy python3-h5py \
      gcc g++ pkg-config libhdf5-dev
    ;;
  *rhel*|*fedora*|*centos*)
    $SUDO dnf install -y wireshark-cli python3 python3-pip python3-devel gcc gcc-c++ pkgconf-pkg-config
    $SUDO dnf install -y python3-numpy || true
    # h5py / hdf5-devel live in EPEL on RHEL
    $SUDO dnf install -y python3-h5py hdf5-devel 2>/dev/null \
      || { $SUDO dnf install -y "https://dl.fedoraproject.org/pub/epel/epel-release-latest-${VERSION_ID%%.*}.noarch.rpm" \
           && $SUDO dnf install -y python3-h5py hdf5-devel; } || true
    ;;
  *suse*|*sles*)
    $SUDO zypper --non-interactive install wireshark python3 python3-pip python3-devel gcc gcc-c++ pkg-config
    $SUDO zypper --non-interactive install python3-numpy python3-h5py hdf5-devel || true
    ;;
  *)
    echo "Unsupported distro '$ID' — install tshark, python3 (>=3.9), numpy and h5py manually." >&2
    ;;
esac

echo "==> Creating virtualenv (reusing distro numpy/h5py when available)"
cd "$APP_DIR"
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --upgrade pip
# Install everything except numpy/h5py first; those come from the distro if possible
grep -vE '^\s*(#|$)|^(numpy|h5py)' requirements-s390x.txt > .venv/requirements-web.txt
.venv/bin/pip install -r .venv/requirements-web.txt
if ! .venv/bin/python -c "import numpy, h5py" 2>/dev/null; then
  echo "==> numpy/h5py not packaged for this distro — building from source (can take 10-20 min)"
  .venv/bin/pip install "numpy>=1.21,<2.0" "h5py>=3.6,<4"
fi

echo "==> Checking the model runs on this machine"
.venv/bin/python - <<'EOF'
import numpy as np, h5py, sys, platform
from app.model_loader import load_model
m = load_model("output/10t-10n-DOS2019-LUCID.h5")
f = h5py.File("sample-dataset/10t-10n-DOS2019-dataset-test.hdf5", "r")
X, y = np.array(f["set_x"][:]), np.array(f["set_y"][:])
acc = float((np.squeeze(m.predict(X) > 0.5) == y).mean())
print(f"   backend={type(m).__name__} arch={platform.machine()} byteorder={sys.byteorder} test_accuracy={acc:.4f}")
if acc < 0.95:
    sys.exit("Model accuracy unexpectedly low — check numpy/h5py installation")
EOF

echo "==> Installing systemd service 'lucid-ddos' on port $PORT"
$SUDO tee /etc/systemd/system/lucid-ddos.service >/dev/null <<EOF
[Unit]
Description=LUCID DDoS detection dashboard
After=network-online.target

[Service]
User=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host $HOST --port $PORT
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
$SUDO systemctl daemon-reload
$SUDO systemctl enable --now lucid-ddos
$SUDO systemctl restart lucid-ddos

if [ "$PUBLIC" = "1" ]; then
  echo "==> PUBLIC=1: opening port $PORT in the firewall (if one is active)"
  if command -v firewall-cmd >/dev/null && $SUDO firewall-cmd --state >/dev/null 2>&1; then
    $SUDO firewall-cmd --permanent --add-port="$PORT/tcp" && $SUDO firewall-cmd --reload
  elif command -v ufw >/dev/null && $SUDO ufw status | grep -q "Status: active"; then
    $SUDO ufw allow "$PORT/tcp"
  fi
fi

sleep 3
if curl -fsS -o /dev/null "http://127.0.0.1:$PORT/" || curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/" | grep -q 30; then
  echo
  if [ "$PUBLIC" = "1" ]; then
    echo "LUCID-DDoS is running publicly:  http://$(hostname -I | awk '{print $1}'):$PORT"
  else
    echo "LUCID-DDoS is running privately on 127.0.0.1:$PORT (not reachable from the internet)."
    echo "From your own computer run:"
    echo "  ssh -i <key.pem> -L $PORT:127.0.0.1:$PORT $RUN_USER@<server-ip>"
    echo "then open http://localhost:$PORT"
  fi
  echo "Logs:    sudo journalctl -u lucid-ddos -f"
  echo "Restart: sudo systemctl restart lucid-ddos"
else
  echo "Service did not respond — check: sudo journalctl -u lucid-ddos -n 50" >&2
  exit 1
fi
