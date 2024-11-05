FROM ubuntu:22.04

RUN apt update && \
	apt install -y python3 python3-pip python3-venv && \
	rm -rf /var/lib/apt/lists/* && \
	python3 -m venv /venv && \
	/venv/bin/pip install --upgrade pip

COPY requirements.txt /requirements.txt

RUN /venv/bin/pip install -r /requirements.txt

COPY . .

EXPOSE 8000

CMD ["venv/bin/gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--threads", "4", "--worker-connections", "1000", "--max-requests", "1000", "--timeout", "60", "--keep-alive", "10", "app:app"]