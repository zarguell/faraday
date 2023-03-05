######################## Base Args ########################
ARG BASE_REGISTRY=docker.io
ARG BASE_IMAGE=zarguell/ubi8
ARG BASE_TAG=latest

FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG}

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

COPY server.ini /home/faraday/.faraday/config/server.ini
RUN chown faraday:faraday /home/faraday/.faraday/config/server.ini

USER faraday
RUN /opt/faraday/bin/faraday-manage create-tables

CMD ["/opt/faraday/bin/faraday-server"]
