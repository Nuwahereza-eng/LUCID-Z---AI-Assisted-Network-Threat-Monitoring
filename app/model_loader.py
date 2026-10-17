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


def load_model(path: str):
    tflite_path = os.path.splitext(path)[0] + ".tflite"
    if path.endswith(".tflite"):
        tflite_path = path
    if os.path.isfile(tflite_path):
        interpreter_cls = _tflite_interpreter_cls()
        if interpreter_cls is not None:
            logger.info(f"Using TFLite model: {tflite_path}")
            return TFLiteModel(tflite_path, interpreter_cls)
    from tensorflow.keras.models import load_model as keras_load_model
    return keras_load_model(path)
