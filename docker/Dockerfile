FROM debian:bookworm AS wine
LABEL org.opencontainers.image.authors="Tobias Gruetzmacher <tobias-docker@23.gs>"

ENV DEBIAN_FRONTEND=noninteractive

# renovate: datasource=github-releases depName=krallin/tini
ARG TINI_VERSION=0.19.0

ADD https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini /tini
RUN chmod +x /tini

COPY apt /etc/apt

RUN \
	dpkg --add-architecture i386 \
	&& apt-get update -y \
	&& apt-get install -y --no-install-recommends \
		ca-certificates \
		curl \
		libvulkan1 \
		unzip \
		xauth \
		xvfb \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY fix-xvfb.sh /tmp/

ARG WINE_FLAVOUR=devel

RUN \
	/tmp/fix-xvfb.sh \
	&& sed -i '/^Enabled:/ s/no/yes/' /etc/apt/sources.list.d/* \
	&& apt-get update -y \
	&& apt-get install -y --no-install-recommends \
		winehq-${WINE_FLAVOUR} \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

FROM wine

ENV WINEDEBUG=-all
ENV WINEPREFIX=/opt/wineprefix

COPY wine-init.sh keys.gpg /tmp/helper/
COPY mkuserwineprefix entrypoint.sh /opt/

# Prepare environment
RUN xvfb-run sh /tmp/helper/wine-init.sh

# renovate: datasource=github-tags depName=python/cpython versioning=pep440
ARG PYTHON_VERSION=3.13.5
# renovate: datasource=github-releases depName=upx/upx versioning=loose
ARG UPX_VERSION=5.0.1

RUN umask 0 && cd /tmp/helper && \
  curl --fail-with-body -LOOO \
    https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe{,.asc} \
  && \
  gpgv --keyring ./keys.gpg python-${PYTHON_VERSION}-amd64.exe.asc python-${PYTHON_VERSION}-amd64.exe && \
  xvfb-run sh -c "\
    wine python-${PYTHON_VERSION}-amd64.exe /quiet TargetDir=C:\\Python \
      Include_doc=0 InstallAllUsers=1 PrependPath=1; \
    wineserver -w" && \
  cd .. && rm -Rf helper

# Install some python software
RUN umask 0 && xvfb-run sh -c "\
  wine pip install --no-warn-script-location pyinstaller; \
  wineserver -w"

ENTRYPOINT ["/opt/entrypoint.sh"]