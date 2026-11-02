FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libegl1 libgl1 libgomp1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . /app
USER app
ENV HOME=/home/app OMP_NUM_THREADS=2
EXPOSE 7860
CMD ["python", "server.py", "--cloud", "--port", "7860", "--data", "/home/app/lidarmonk-data"]
