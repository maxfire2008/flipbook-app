# syntax=docker/dockerfile:1

FROM python:3.11-slim

LABEL org.opencontainers.image.source https://github.com/maxfire2008/flipbook-app

RUN apt-get update && apt-get install -y git

ENV TZ="Australia/Hobart"

WORKDIR /app

RUN pip3 install flask flask_wtf wtforms gunicorn pyyaml sqlalchemy

COPY . /app

CMD [ "gunicorn", "-b" , "0.0.0.0:3547", "--workers=4", "app:app", "--log-level", "DEBUG", "--reload"]
