FROM python:3.10.1-alpine

RUN mkdir -p /opt/tempo-check
WORKDIR /opt/tempo-check

COPY requirements.txt /opt/tempo-check/
RUN pip install -r /opt/tempo-check/requirements.txt