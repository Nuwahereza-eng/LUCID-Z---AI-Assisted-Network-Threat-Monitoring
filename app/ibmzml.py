"""
IBM Machine Learning for z/OS — Scoring Client
===============================================

IBM Machine Learning for z/OS (IBM z/OS ML) allows you to deploy trained models
and serve them via a REST scoring API directly on the mainframe, co-located with
your transactional workloads (CICS, Db2, IMS).

Reference:
  https://www.ibm.com/docs/en/machine-learning-for-zos

How this integrates with LUCID-DDoS
-------------------------------------
LUCID trains a CNN that classifies network flows as benign or DDoS. Once that
model is deployed to IBM ML for z/OS (as an ONNX or PMML asset), each detection
window can send its feature matrix to the z/OS scoring endpoint instead of — or
alongside — the local TensorFlow model.

This achieves **Transactional AI**: the inference decision happens inside the
mainframe's transaction processing environment, with sub-millisecond round-trips
to the data, rather than requiring data to leave the enterprise boundary.

Scoring endpoint contract (IBM z/OS ML REST API):
  POST https://<zos-host>:<port>/v1/model/<model-id>/predict
  Authorization: Bearer <JWT>
  Content-Type: application/json

  Body:
  {
    "input_data": [
      {
        "fields": ["f0","f1",...,"f109"],   // flattened fragment features
        "values": [[...], [...], ...]        // one row per fragment
      }
    ]
  }

  Response:
  {
    "predictions": [
      {
        "fields": ["prediction", "probability"],
        "values": [[1, 0.92], [0, 0.03], ...]
      }
    ]
  }

Configuration (environment variables):
  IBMZML_SCORING_URL   Full URL to the z/OS ML scoring endpoint
                       e.g. https://zos-host:12345/v1/model/ddos-lucid/predict
  IBMZML_TOKEN         Bearer JWT token (obtain from z/OS ML authentication)
  IBMZML_VERIFY_TLS    Set to "false" to skip TLS verification (dev/test only)
  IBMZML_TIMEOUT_SEC   Per-request timeout in seconds (default: 5)

If IBMZML_SCORING_URL is not set the client returns None and the caller falls
back to local TensorFlow inference automatically.
"""

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lucid-ibmzml")


class IBMZMLClient:
    """Thin client for IBM Machine Learning for z/OS scoring REST API."""

    def __init__(self):
        self.scoring_url: Optional[str] = os.environ.get("IBMZML_SCORING_URL", "").strip() or None
        self.token: Optional[str] = os.environ.get("IBMZML_TOKEN", "").strip() or None
        self.verify_tls: bool = os.environ.get("IBMZML_VERIFY_TLS", "true").strip().lower() not in ("false", "0", "no")
        self.timeout: float = float(os.environ.get("IBMZML_TIMEOUT_SEC", "5"))

    @property
    def configured(self) -> bool:
        """True when the scoring URL is set — i.e., z/OS ML is available."""
        return bool(self.scoring_url)

    def score(self, X_flat: List[List[float]]) -> Optional[Dict[str, Any]]:
        """Send a batch of flattened feature vectors to IBM ML for z/OS.

        Parameters
        ----------
        X_flat : list of lists
            Each inner list is a flattened fragment (max_flow_len * 11 values).

        Returns
        -------
        dict with keys:
            predictions  : list of int  (0=benign, 1=ddos)
            probabilities: list of float
            latency_sec  : float
            engine       : "ibmzml"
        or None if the client is not configured or the call fails.
        """
        if not self.configured:
            return None

        # Build IBM z/OS ML request body
        n_features = len(X_flat[0]) if X_flat else 0
        fields = [f"f{i}" for i in range(n_features)]
        payload = {
            "input_data": [
                {
                    "fields": fields,
                    "values": X_flat,
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(
            self.scoring_url, data=body, headers=headers, method="POST"
        )

        # Disable TLS verification for dev/test environments if requested
        if not self.verify_tls:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx = None  # type: ignore[assignment]

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                raw = resp.read().decode("utf-8")
            latency = time.time() - t0
        except urllib.error.HTTPError as e:
            logger.warning(f"IBM z/OS ML scoring HTTP error {e.code}: {e.read().decode('utf-8', errors='replace')}")
            return None
        except Exception as e:
            logger.warning(f"IBM z/OS ML scoring failed: {e}")
            return None

        try:
            result = json.loads(raw)
            rows = result["predictions"][0]["values"]
            # Each row: [prediction_label, probability_of_positive]
            predictions = [int(row[0]) for row in rows]
            probabilities = [float(row[1]) if len(row) > 1 else float(row[0]) for row in rows]
        except (KeyError, IndexError, ValueError) as e:
            logger.warning(f"IBM z/OS ML unexpected response shape: {e} — raw: {raw[:200]}")
            return None

        return {
            "predictions": predictions,
            "probabilities": probabilities,
            "latency_sec": latency,
            "engine": "ibmzml",
            "endpoint": self.scoring_url,
        }

    def health(self) -> Dict[str, Any]:
        """Return configuration and reachability status for the dashboard."""
        if not self.configured:
            return {
                "configured": False,
                "message": (
                    "IBM ML for z/OS scoring is not configured. "
                    "Set IBMZML_SCORING_URL and IBMZML_TOKEN to enable. "
                    "When configured, LUCID will route detection windows through the z/OS scoring endpoint "
                    "instead of the local TensorFlow model, enabling Transactional AI on IBM Z."
                ),
            }
        # Attempt a lightweight connectivity check (HEAD or OPTIONS)
        try:
            req = urllib.request.Request(self.scoring_url, method="HEAD")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            if not self.verify_tls:
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            else:
                ctx = None  # type: ignore[assignment]
            with urllib.request.urlopen(req, timeout=3, context=ctx):
                reachable = True
        except Exception:
            reachable = False

        return {
            "configured": True,
            "endpoint": self.scoring_url,
            "reachable": reachable,
            "tls_verify": self.verify_tls,
            "message": (
                "IBM ML for z/OS is configured and reachable. "
                "Detection windows will be scored on IBM Z."
            ) if reachable else (
                "IBM ML for z/OS is configured but endpoint is not reachable. "
                "Falling back to local TensorFlow inference. "
                "Check IBMZML_SCORING_URL and network connectivity."
            ),
        }


# Module-level singleton — imported by main.py
zml_client = IBMZMLClient()
