FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 5000
CMD ["./entrypoint.sh"]