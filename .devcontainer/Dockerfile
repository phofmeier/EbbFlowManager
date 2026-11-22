FROM mcr.microsoft.com/devcontainers/base:ubuntu

ARG NODE_VERSION=26
ARG NVM_VERSION=0.41.0
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

USER ${USERNAME}

# Install NVM
ENV NVM_DIR=/home/${USERNAME}/.nvm
ENV BASH_ENV=/home/${USERNAME}/.bash_env

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN touch "$BASH_ENV" \
    && echo '. "$NVM_DIR/nvm.sh"' >> "$BASH_ENV"

RUN curl -fsSL \
    "https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh" \
    | PROFILE="$BASH_ENV" bash

RUN nvm install "$NODE_VERSION" \
    && nvm alias default "$NODE_VERSION"

ENV PATH="/home/${USERNAME}/.nvm/versions/node/$(cat /home/${USERNAME}/.nvm/alias/default)/bin:${PATH}"

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

RUN uv python install "$PYTHON_VERSION"

# Install OpenCode if requested
ENV PATH="/home/${USERNAME}/.local/bin:/home/${USERNAME}/.opencode/bin:${PATH}"
RUN if [ "${INSTALL_OPENCODE}" = "true" ]; then \
        curl -fsSL https://opencode.ai/v2/install | OPENCODE_VERSION="${OPENCODE_VERSION}" bash -s -- --no-modify-path; \
    else \
        echo "OpenCode installation disabled"; \
    fi

# Configure Bash and Zsh
RUN for shell_config in /home/${USERNAME}/.bashrc /home/${USERNAME}/.zshrc; do \
        echo '[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"' >> "$shell_config"; \
    done

WORKDIR /workspace

RUN node --version \
    && npm --version \
    && uv --version
