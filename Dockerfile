FROM python:3.11-slim-trixie
LABEL  maintainer="ys33ys33ys55@gmail.com"

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

ENV UV_NO_DEV=1

COPY web_entrypoint.sh web_entrypoint.sh
RUN chmod +x web_entrypoint.sh
RUN uv sync

ENTRYPOINT ["./web_entrypoint.sh"]
