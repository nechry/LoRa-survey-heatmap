FROM python:3.8-slim-buster

USER root

WORKDIR /app

RUN python -m pip install -U pip
RUN python -m pip install matplotlib scipy wheel libnl3


COPY setup.cfg setup.cfg
COPY setup.py setup.py
COPY README.md README.md
COPY src/heatmap.py heatmap.py
COPY src/thresholds.py thresholds.py

RUN python3 setup.py develop
RUN pip3 freeze > /app/requirements.installed

LABEL maintainer="nechry@gmail.com" \
      org.label-schema.name="nechry/python-lora-survey-heatmap" \
      org.label-schema.schema-version="1.0"

CMD /bin/bash
