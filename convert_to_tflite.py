"""Convert a LUCID Keras .h5 model to .tflite (needs full TensorFlow).

Usage: python convert_to_tflite.py output/10t-10n-DOS2019-LUCID.h5
Writes the .tflite file next to the .h5; app/model_loader.py picks it up.
"""
import os
import sys

import tensorflow as tf

src = sys.argv[1] if len(sys.argv) > 1 else "output/10t-10n-DOS2019-LUCID.h5"
dst = os.path.splitext(src)[0] + ".tflite"
model = tf.keras.models.load_model(src)
tflite = tf.lite.TFLiteConverter.from_keras_model(model).convert()
with open(dst, "wb") as f:
    f.write(tflite)
print(f"Wrote {dst} ({len(tflite)} bytes)")
