FROM python:3.10-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-rus \
    chromium \
    libgl1 libglib2.0-0 libxrender1 libsm6 libxext6 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/backend

ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["python", "-m", "backend.app"]
