FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
COPY docs ./docs
COPY src ./src
COPY streamlit_app ./streamlit_app
COPY data/sample ./data/sample

EXPOSE 8000 8501
