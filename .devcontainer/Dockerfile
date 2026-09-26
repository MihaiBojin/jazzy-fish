ARG VARIANT
FROM mcr.microsoft.com/devcontainers/python:1-${VARIANT}

# Additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    fzf \
    gnupg2 \
    jq \
    vim \
    ;

# Install shellcheck. The architecture is not hardcoded: the devcontainer builds
# on arm64 hosts too, where the x86_64 tarball produced an unusable binary.
RUN scversion="stable" && \
    case "$(dpkg --print-architecture)" in \
    amd64) scarch="x86_64" ;; \
    arm64) scarch="aarch64" ;; \
    *) echo "unsupported architecture: $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac && \
    wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${scversion?}/shellcheck-${scversion?}.linux.${scarch}.tar.xz" | tar -xJv && \
    cp "shellcheck-${scversion}/shellcheck" /usr/bin/ && \
    rm -rf "shellcheck-${scversion}" && \
    shellcheck --version

USER vscode
