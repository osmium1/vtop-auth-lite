import onnxruntime as ort
import io
import numpy as np
from PIL import Image

# Configuration Constants (Matches original trained weights)
IMG_WIDTH = 150
IMG_HEIGHT = 50
CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

class CaptchaSolver:
    """
    Extremely lightweight CAPTCHA solver using ONNX Runtime.
    Reduces RAM usage from ~200MB (PyTorch) to ~40MB.
    """
    def __init__(self, model_path=None):
        if model_path is None:
            import os
            base_dir = os.path.dirname(__file__)
            model_path = os.path.join(base_dir, "models", "captcha_crnn.onnx")
            
        # Prefer GPU if available, fallback to CPU
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(model_path, providers=providers)
        except Exception:
            # Fallback for systems without CUDA
            self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            
        self.input_name = self.session.get_inputs()[0].name
        
    def decode_prediction(self, output):
        """Greedy CTC decoding for ONNX output."""
        # output: (Seq, Batch, Classes) -> (37, 1, 37)
        output = output.squeeze(1) # (37, 37)
        # Use numpy for softmax/argmax to avoid torch dependency
        # Actually, greedy CTC only needs argmax
        preds = np.argmax(output, axis=1)
        
        res = []
        last_char = -1
        for p in preds:
            if p != 0 and p != last_char:
                # index 0 is blank, index 1 is CHARACTERS[0]
                res.append(CHARACTERS[p - 1])
            last_char = p
        return "".join(res)

    def solve(self, img_bytes: bytes) -> str:
        """Solves a CAPTCHA image using ONNX Runtime."""
        try:
            # 1. Preprocess using PIL & Numpy
            img = Image.open(io.BytesIO(img_bytes)).convert('L').resize((IMG_WIDTH, IMG_HEIGHT))
            img_np = np.array(img).astype(np.float32) / 255.0
            
            # Normalization (Matches training): (x - 0.5) / 0.5
            img_tensor = (img_np[np.newaxis, np.newaxis, :, :] - 0.5) / 0.5
            
            # 2. Run Inference
            # input shape must be (Batch, 1, 50, 150)
            outputs = self.session.run(None, {self.input_name: img_tensor})
            
            # 3. Decode
            prediction = self.decode_prediction(outputs[0])
            
            return prediction.strip().upper()
        except Exception as e:
            return f"ERROR: {e}"
