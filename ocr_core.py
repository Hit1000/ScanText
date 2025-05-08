from PIL import Image
import pytesseract
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import LSTM


def custom_ocr_core(file):

    def preprocess_image(image_path):
        image = Image.open(image_path).convert("L")
        image = image.resize((IMG_WIDTH, IMG_HEIGHT))
        image = img_to_array(image) / 255.0
        image = np.expand_dims(image, axis=0)  # Batch size = 1
        return image

    ocr_model = load_model("models/best_model.h5", custom_objects={'LSTM': LSTM})

    IMG_WIDTH = 128
    IMG_HEIGHT = 32

    img = preprocess_image(file_path)
    preds = ocr_model.predict(img)

    if isinstance(preds, str):
        return preds

    decoded = ''.join([chr(np.argmax(p)) for p in preds[0]])
    return decoded.strip()

def ocr_core(file, lang):
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    text = pytesseract.image_to_string(Image.open(file),lang=lang, config='--psm 3')
    return text