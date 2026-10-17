"""Model loading with a lightweight TFLite path for low-memory hosting.

`load_model(path)` takes the usual Keras `.h5` path. If a sibling `.tflite`
file exists and a TFLite runtime is installed (`ai-edge-litert` or
`tflite-runtime`), the model is served through it instead of full TensorFlow,
cutting memory use from ~400 MB to a few MB. Otherwise falls back to Keras.

Generate the `.tflite` file with: python convert_to_tflite.py <model.h5>
"""
import logging
import os

import numpy as np

logger = logging.getLogger("lucid.model")


def _tflite_interpreter_cls():
    try:
        from ai_edge_litert.interpreter import Interpreter
        return Interpreter
    except ImportError:
        pass
    try:
        from tflite_runtime.interpreter import Interpreter
        return Interpreter
    except ImportError:
        return None


class TFLiteModel:
    """Minimal stand-in for a Keras model exposing `predict(X, batch_size)`."""

    def __init__(self, path: str, interpreter_cls):
        self.path = path
        self._interp = interpreter_cls(model_path=path)
        self._in = self._interp.get_input_details()[0]
        self._out = self._interp.get_output_details()[0]
        self._batch = None

    def _ensure_batch(self, n: int):
        if self._batch != n:
            shape = list(self._in["shape"])
            shape[0] = n
            self._interp.resize_tensor_input(self._in["index"], shape)
            self._interp.allocate_tensors()
            self._batch = n

    def predict(self, X, batch_size: int = 2048, **_kwargs):
        X = np.asarray(X, dtype=self._in["dtype"])
        # Keras tolerates a missing trailing channel axis; TFLite does not
        if X.ndim == len(self._in["shape"]) - 1:
            X = X[..., np.newaxis]
        if len(X) == 0:
            return np.zeros((0,) + tuple(self._out["shape"][1:]), dtype=np.float32)
        outs = []
        for i in range(0, len(X), batch_size):
            chunk = X[i:i + batch_size]
            self._ensure_batch(len(chunk))
            self._interp.set_tensor(self._in["index"], chunk)
            self._interp.invoke()
            outs.append(self._interp.get_tensor(self._out["index"]).copy())
        return np.concatenate(outs, axis=0)


class NumpyLucidModel:
    """Pure-NumPy inference for the LUCID topology, read straight from the .h5.

    Supports Conv2D(valid, stride 1) -> ReLU -> GlobalMaxPooling2D -> Dense(sigmoid),
    with optional Flatten/Dropout. Needs only numpy + h5py, so it runs on
    platforms without TensorFlow or TFLite wheels (e.g. IBM Z / LinuxONE s390x).
    """

    _PASSTHROUGH = {"InputLayer", "Flatten", "Dropout"}

    def __init__(self, path: str):
        import json
        import h5py

        self.path = path
        with h5py.File(path, "r") as f:
            cfg = f.attrs["model_config"]
            cfg = json.loads(cfg.decode() if isinstance(cfg, bytes) else cfg)
            layers = [l for l in cfg["config"]["layers"] if l["class_name"] not in self._PASSTHROUGH]
            kinds = [l["class_name"] for l in layers]
            conv, dense = layers[0]["config"], layers[-1]["config"]
            supported = (
                kinds in (["Conv2D", "Activation", "GlobalMaxPooling2D", "Dense"],
                          ["Conv2D", "GlobalMaxPooling2D", "Dense"])
                and tuple(conv.get("strides", (1, 1))) == (1, 1)
                and conv.get("padding") == "valid"
                and conv.get("data_format", "channels_last") == "channels_last"
                and dense.get("activation") == "sigmoid"
            )
            conv_act = conv.get("activation", "linear")
            if kinds[1] == "Activation":
                if conv_act != "linear":
                    supported = False
                conv_act = layers[1]["config"]["activation"]
            if not supported or conv_act not in ("relu", "linear"):
                raise ValueError(f"Unsupported model topology for NumPy backend: {kinds}")
            self._relu = conv_act == "relu"

            def weights(layer_name):
                found = {}

                def collect(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        found[name.rsplit("/", 1)[-1].split(":")[0]] = obj[()]

                f["model_weights"][layer_name].visititems(collect)
                # astype(np.float32) converts the file's little-endian data to native order (s390x is big-endian)
                return found["kernel"].astype(np.float32), found.get("bias", np.zeros(1, np.float32)).astype(np.float32)

            self._ck, self._cb = weights(layers[0]["config"]["name"])  # (kh, kw, cin, filters)
            self._dk, self._db = weights(layers[-1]["config"]["name"])  # (filters, 1)

    def predict(self, X, batch_size: int = 2048, **_kwargs):
        X = np.asarray(X, dtype=np.float32)
        if X.ndim == 3:
            X = X[..., np.newaxis]
        kh, kw, cin, nf = self._ck.shape
        n, h, w, _ = X.shape
        if n == 0:
            return np.zeros((0, 1), dtype=np.float32)
        kernel = self._ck.reshape(kh * kw * cin, nf)
        outs = []
        for i in range(0, n, batch_size):
            xb = X[i:i + batch_size]
            # im2col: every valid (kh x kw) patch, flattened in kernel order
            patches = np.lib.stride_tricks.sliding_window_view(xb, (kh, kw), axis=(1, 2))
            # (b, h-kh+1, w-kw+1, cin, kh, kw) -> (b, oh, ow, kh, kw, cin)
            patches = patches.transpose(0, 1, 2, 4, 5, 3).reshape(len(xb), -1, kh * kw * cin)
            conv = patches @ kernel + self._cb
            if self._relu:
                conv = np.maximum(conv, 0)
            pooled = conv.max(axis=1)
            logits = pooled @ self._dk + self._db
            outs.append(np.exp(-np.logaddexp(0, -logits)))  # overflow-safe sigmoid
        return np.concatenate(outs, axis=0).astype(np.float32)


def load_model(path: str):
    """Load a model, preferring backends that don't need full TensorFlow.

    Order: TFLite (sibling .tflite + runtime installed) -> pure NumPy
    (supported LUCID topology) -> Keras. Set LUCID_MODEL_BACKEND to
    tflite | numpy | keras to force one.
    """
    forced = os.environ.get("LUCID_MODEL_BACKEND", "").strip().lower()
    tflite_path = path if path.endswith(".tflite") else os.path.splitext(path)[0] + ".tflite"

    if forced in ("", "tflite") and os.path.isfile(tflite_path):
        interpreter_cls = _tflite_interpreter_cls()
        if interpreter_cls is not None:
            logger.info(f"Using TFLite model: {tflite_path}")
            return TFLiteModel(tflite_path, interpreter_cls)
    if forced in ("", "numpy") and path.endswith(".h5"):
        try:
            model = NumpyLucidModel(path)
            logger.info(f"Using NumPy model backend: {path}")
            return model
        except Exception as e:
            if forced == "numpy":
                raise
            logger.info(f"NumPy backend unavailable ({e}); falling back to Keras")
    from tensorflow.keras.models import load_model as keras_load_model
    return keras_load_model(path)
