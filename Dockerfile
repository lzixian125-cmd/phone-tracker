FROM python:3.11-slim
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
