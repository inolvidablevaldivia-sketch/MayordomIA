FROM python:3.12-slim

# Sistema de OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn gunicorn pydantic pydantic-settings python-dotenv python-telegram-bot "google-genai>=1.0.0" firebase-admin httpx python-multipart python-jose python-dateutil pendulum openpyxl Pillow pytesseract pdf2image

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
