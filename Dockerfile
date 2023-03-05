######################## Base Args ########################
ARG BASE_REGISTRY=docker.io
ARG BASE_IMAGE=zarguell/ubi8
ARG BASE_TAG=latest

FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG}

COPY ./docker/entrypoint.sh /entrypoint.sh
COPY ./docker/server.ini /docker_server.ini

RUN dnf update -y --nodocs && \
		dnf clean all && \
		rm -rf /var/cache/yum && \
		dnf remove -y vim-minimal

RUN dnf install -y mailcap wget \
 && RELEASE_URL=$(curl -s https://api.github.com/repos/infobyte/faraday/releases/latest | grep "browser_download_url.*\.rpm" | cut -d : -f 2,3 | tr -d \") \
 && wget $RELEASE_URL \
 && rpm -ivh faraday-server_amd64.rpm \
 && rm -f faraday-server_amd64.rpm \
 && chown -R faraday:faraday /home/faraday/
 && chown faraday:faraday /entrypoint.sh
 && chown faraday:faraday /docker_server.ini

USER faraday
WORKDIR /home/faraday

RUN mkdir -p /home/faraday/.faraday/config
RUN mkdir -p /home/faraday/.faraday/logs
RUN mkdir -p /home/faraday/.faraday/session
RUN mkdir -p /home/faraday/.faraday/storage


ENV PYTHONUNBUFFERED 1
ENV FARADAY_HOME /home/faraday

EXPOSE 5985
EXPOSE 9000

ENTRYPOINT ["/entrypoint.sh"]