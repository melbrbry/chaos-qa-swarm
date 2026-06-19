FROM python:3.12-slim

WORKDIR /app

COPY target_app/ target_app/

RUN pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn[standard]>=0.32.0"

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "target_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
