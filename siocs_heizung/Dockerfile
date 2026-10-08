FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

RUN pip install --no-cache-dir playwright==1.48.0 aiohttp==3.10.10

COPY run.py /run.py

CMD ["python3", "-u", "/run.py"]
