# Use a lightweight Python 3.13 image (ARM compatible for Raspberry Pi)
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Install system dependencies required for Playwright & OCR tools
RUN apt update && apt install -y \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libgtk-3-0 libasound2 \
    tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Ensure Tesseract can find language data
ENV TESSDATA_PREFIX="/usr/share/tesseract-ocr/5/tessdata"

# Install uv (instead of PDM)
RUN pip install --no-cache-dir uv

# Copy dependency file (assuming you have a requirements.txt or pyproject.toml for uv)
COPY pyproject.toml README.md ./

# Install dependencies using uv
RUN uv sync

# Copy the rest of the application code
COPY . .

# Start the Discord bot using uv
CMD ["uv", "run", "src/app.py"]
