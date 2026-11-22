FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt \
    && groupadd --system app && useradd --system --gid app --home-dir /app app
COPY docs ./docs
COPY src ./src
COPY streamlit_app ./streamlit_app
COPY data/sample ./data/sample
RUN mkdir -p data/raw && chown -R app:app /app
USER app

EXPOSE 8000 8501
