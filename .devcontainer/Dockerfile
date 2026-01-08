# Hansard Tales Development Container
# Matches GitHub Actions ubuntu-latest environment

FROM mcr.microsoft.com/vscode/devcontainers/base:jammy

# Set environment variables
ENV GO_VERSION=1.21.6
ENV PYTHON_VERSION=3.11
ENV NODE_VERSION=18
ENV DEBIAN_FRONTEND=noninteractive

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    postgresql-client \
    redis-tools \
    jq \
    bc \
    zip \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.21
RUN wget -q https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz \
    && rm go${GO_VERSION}.linux-amd64.tar.gz

# Add Go to PATH
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GOCACHE="/go/cache"

# Install Go tools
RUN go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Install Python 3.11 and pip
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    python3.11-distutils \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip3 install --upgrade pip setuptools wheel \
    && pip3 install black flake8 mypy pre-commit pytest pytest-cov pytest-mock pytest-asyncio

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install global Node.js tools
RUN npm install -g npm@latest \
    && npm install -g prettier eslint typescript ts-node @types/node

# Create workspace directories
RUN mkdir -p /workspace \
    && mkdir -p /go/pkg \
    && mkdir -p /go/bin \
    && mkdir -p /root/.cache/go-build

# Set up Git configuration (for devcontainer)
RUN git config --global --add safe.directory /workspaces/hansard-tales

# Create cache directories for bind mounts
RUN mkdir -p /go /root/.npm /root/.cache

# Set working directory
WORKDIR /workspaces/hansard-tales

# Copy setup scripts and make executable
COPY tools/local-setup.sh /usr/local/bin/setup-dev-env
RUN chmod +x /usr/local/bin/setup-dev-env

# Set up environment variables for development
ENV NODE_ENV=development
ENV GO111MODULE=on
ENV CGO_ENABLED=1

# Install Docker Compose for local services
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Verify installations
RUN go version \
    && python3 --version \
    && node --version \
    && npm --version \
    && docker-compose --version \
    && golangci-lint --version

# Set up shell environment
RUN echo 'export PATH="/usr/local/go/bin:$PATH"' >> /root/.bashrc \
    && echo 'export GOPATH="/go"' >> /root/.bashrc \
    && echo 'export GOCACHE="/go/cache"' >> /root/.bashrc \
    && echo 'alias ll="ls -la"' >> /root/.bashrc \
    && echo 'alias python=python3' >> /root/.bashrc

# Create helpful development aliases
RUN echo 'alias test-all="./tools/run-local-tests.sh"' >> /root/.bashrc \
    && echo 'alias test-go="cd data-processing/go-functions && ./test.sh"' >> /root/.bashrc \
    && echo 'alias test-python="cd data-processing/python-functions && ./test.sh"' >> /root/.bashrc \
    && echo 'alias test-frontend="cd frontend/web && ./test.sh"' >> /root/.bashrc

# Expose ports for development services
EXPOSE 3000 5432 6379 4566 8080

# Start command
CMD ["/bin/bash"]
