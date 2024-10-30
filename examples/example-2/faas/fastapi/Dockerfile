# Base watchdog and python images
ARG PYTHON_VERSION=3
FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/classic-watchdog:0.3.1 AS watchdog
FROM --platform=${TARGETPLATFORM:-linux/amd64} python:${PYTHON_VERSION}-alpine

ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Allows you to add additional packages via build-arg
ARG ADDITIONAL_PACKAGE

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog
RUN apk --no-cache add ca-certificates ${ADDITIONAL_PACKAGE}

# set work directory
WORKDIR /src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy requirements file
COPY ./requirements.txt /src/requirements.txt

# install dependencies
# RUN set -eux \
#     && apk add --no-cache --virtual .build-deps build-base \
#     libressl-dev libffi-dev gcc musl-dev python3-dev \
#     postgresql-dev \
#     && pip install --upgrade pip setuptools wheel \
#     && pip install -r /src/requirements.txt \
#     && rm -rf /root/.cache/pip
RUN pip install -r /src/requirements.txt
RUN pip install waitress

# copy project
COPY . /src/

# What to run to handle request
ENV fprocess="python -m app.main"
ENV cgi_headers="true"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:8080"
ENV write_debug="false"

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]