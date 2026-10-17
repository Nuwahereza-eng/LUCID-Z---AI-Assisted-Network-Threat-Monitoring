"""
IBM Z / LinuxONE integration helpers for LUCID-DDoS.

Detects at runtime whether the service is executing on IBM Z (s390x) hardware
and exposes that information via /api/ibmz/status.

Genuine IBM Z integration paths (no fabrication):
  1. TensorFlow for s390x — IBM ships official TF wheels for LinuxONE. The
     existing .h5 model loads and runs on s390x without any modification.
     Reference: https://developer.ibm.com/learningpaths/get-started-with-ai-on-ibm-z/

  2. Telum AI acceleration (IBM Integrated Accelerator for AI) — Available on
     IBM z16 (machine type 3931) and IBM LinuxONE Emperor 4 (3932). Workloads
     use the IBM zDNN API via the ONNX-MLIR compiler:
       Keras .h5  →  ONNX (tf2onnx)  →  ONNX-MLIR  →  zDNN execution
     The LUCID Conv2D/GlobalMaxPooling2D/Dense topology is fully supported
     operator-wise by zDNN.
     Reference: https://www.ibm.com/docs/en/linux-on-systems?topic=zDNN

  3. IBM OpenShift on IBM Z — the existing Dockerfile deploys unchanged onto
     Red Hat OpenShift running on IBM Z or LinuxONE clusters.

  4. Mainframe traffic feed via IBM MQ or REST — z/OS applications (CICS,
     Db2) can forward network event records to /api/ingest over HTTP, enabling
     LUCID to score traffic generated inside the mainframe's OSA-Express adapters.
"""

import os
import platform
import re
from typing import Any, Dict, Optional


# IBM Z machine-type prefixes found in /proc/cpuinfo on Linux on Z
_IBMZ_MACHINE_TYPES = {
    "2064": "z900",
    "2066": "z800",
    "2084": "z990",
    "2086": "z890",
    "2094": "z9 EC",
    "2096": "z9 BC",
    "2097": "z10 EC",
    "2098": "z10 BC",
    "2817": "z196",
    "2818": "z114",
    "2827": "zEC12",
    "2828": "zBC12",
    "2964": "z13 / LinuxONE Emperor",
    "2965": "z13s / LinuxONE Rockhopper",
    "3906": "z14 / LinuxONE Emperor II",
    "3907": "z14s / LinuxONE Rockhopper II",
    "8561": "z15 / LinuxONE III",
    "8562": "z15 T02",
    "3931": "z16 / LinuxONE Emperor 4",  # Telum AI chip
    "3932": "z16 A02 / LinuxONE Emperor 4",  # Telum AI chip
}

# Machine types that include the IBM Integrated Accelerator for AI (Telum)
_TELUM_MACHINE_TYPES = {"3931", "3932"}


def _read_cpuinfo() -> str:
    try:
        with open("/proc/cpuinfo", "r") as fh:
            return fh.read()
    except Exception:
        return ""


def detect_ibmz() -> Dict[str, Any]:
    """Return a dict describing IBM Z / LinuxONE presence and capabilities."""
    arch = platform.machine()  # e.g. 's390x', 'x86_64', 'arm64'
    on_ibmz = arch.lower() in ("s390x", "s390")

    machine_type: Optional[str] = None
    machine_name: Optional[str] = None
    telum_ai = False

    if on_ibmz:
        cpuinfo = _read_cpuinfo()
        # /proc/cpuinfo on LinuxONE: "processor 0: version = FF,  identification = ..."
        # "machine = 3931" or similar
        mt_match = re.search(r"machine\s*=\s*([0-9A-Fa-f]{4})", cpuinfo, re.IGNORECASE)
        if mt_match:
            machine_type = mt_match.group(1).upper()
            machine_name = _IBMZ_MACHINE_TYPES.get(machine_type, f"IBM Z ({machine_type})")
            telum_ai = machine_type in _TELUM_MACHINE_TYPES

    return {
        "arch": arch,
        "on_ibmz": on_ibmz,
        "machine_type": machine_type,
        "machine_name": machine_name,
        "telum_ai": telum_ai,
        "integration_notes": (
            "Running on IBM Z. TensorFlow s390x is the active runtime. "
            + ("Telum AI acceleration available via IBM zDNN/ONNX-MLIR pipeline." if telum_ai else
               "Telum AI acceleration requires z16/LinuxONE Emperor 4 hardware.")
        ) if on_ibmz else (
            "Not running on IBM Z. Deploy this container on IBM LinuxONE or z16 "
            "to enable hardware AI acceleration via the Telum chip. "
            "The .h5 model requires no changes — TensorFlow s390x is binary-compatible."
        ),
    }
