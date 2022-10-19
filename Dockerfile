ARG BASE_REGISTRY=docker.io
ARG BASE_IMAGE=zarguell/python39
ARG BASE_TAG=latest

FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG}

## THIS IS Iron Bank version of Dockerfile to be submitted to Iron Bank repo for approval, do not spin this up locally

# ------------------------------------------------------------------------------------------------------------
# Per hardening manifest guidance: https://repo1.dso.mil/dsop/dccscr/-/tree/master/hardening%20manifest

USER 0

WORKDIR /src

COPY . /src
COPY ./docker/entrypoint.sh /entrypoint.sh
COPY ./docker/server.ini /docker_server.ini
# deploy scripts

RUN dnf update -y --nodocs && \
    dnf install -y postgresql-devel git gcc gcc-c++ make && \
    dnf clean all && \
    rm -rf /var/cache/yum

RUN chown -R 1001:1001 /src
RUN chown 1001:1001 /entrypoint.sh
RUN chown 1001:1001 /docker_server.ini
RUN mkdir -p /home/faraday && chown -R 1001:1001 /home/faraday

USER 1001

RUN pip install -U pip --no-cache-dir \
    && pip install . --no-cache-dir \
    && chmod +x /entrypoint.sh

USER 0

RUN rm -rf /src

USER 1001

WORKDIR /home/faraday

RUN mkdir -p /home/faraday/.faraday/config
RUN mkdir -p /home/faraday/.faraday/logs
RUN mkdir -p /home/faraday/.faraday/session
RUN mkdir -p /home/faraday/.faraday/storage

ENV PYTHONUNBUFFERED 1
ENV FARADAY_HOME /home/faraday

ENTRYPOINT ["/entrypoint.sh"]
