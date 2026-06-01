FROM python:3.13-slim

COPY run.sh requirements.txt /

RUN python -m pip install -r /requirements.txt

COPY src /app/

CMD ["bash", "/run.sh"]