FROM node:24-bookworm-slim AS node
FROM ghcr.io/astral-sh/uv:0.7.2 AS uv
FROM mcr.microsoft.com/devcontainers/base:ubuntu

ARG PYTHON_VERSION=3.13
ARG INSTALL_OPENCODE=false
ARG OPENCODE_VERSION=2.0.22

ARG USERNAME=vscode

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    zsh \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
COPY --from=uv /uv /usr/local/bin/uv
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

USER ${USERNAME}

RUN uv python install "$PYTHON_VERSION"

# Install OpenCode if requested
ENV PATH="/home/${USERNAME}/.local/bin:/home/${USERNAME}/.opencode/bin:${PATH}"
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN if [ "${INSTALL_OPENCODE}" = "true" ]; then \
        curl -fsSL https://opencode.ai/v2/install | OPENCODE_VERSION="${OPENCODE_VERSION}" bash -s -- --no-modify-path; \
    else \
        echo "OpenCode installation disabled"; \
    fi

WORKDIR /workspace

RUN node --version \
    && npm --version \
    && uv --version
