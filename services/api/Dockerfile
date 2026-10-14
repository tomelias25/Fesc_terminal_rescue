FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir psycopg2-binary==2.9.10
WORKDIR /app
COPY app.py .
EXPOSE 8081
CMD ["python", "app.py"]
