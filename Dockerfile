FROM python:3.8

WORKDIR /usr/app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY main.py ./
COPY log_helper.py ./
COPY config.json ./

ENTRYPOINT ["python", "main.py"]
