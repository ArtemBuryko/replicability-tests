# The builder image — replicability test 01 · spec DRAFT v0.4 (SPEC.md §2).
# Built once by the operator, before the dry run, from this folder:
#   docker build -f builder.Dockerfile -t rt01-builder:local .
# Both builders run this one image, by its id. Pinned at the build (SPEC.md §9): the base image's digest
# below, and clis/package-lock.json with each package's integrity, written by npm in that image before the build.
FROM node:22-trixie-slim@sha256:8eb619e402eaede1748a3c8173bffab391592812e85136452f781741c7242ddf

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-numpy python3-scipy \
      poppler-utils ripgrep git curl ca-certificates openssl \
 && rm -rf /var/lib/apt/lists/*

# The two CLIs at their pinned releases, from the npm registry, by the lock file.
WORKDIR /opt/clis
COPY clis/package.json clis/package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund && npm cache clean --force
ENV PATH=/opt/clis/node_modules/.bin:$PATH
RUN codex --version && gemini --version

# The image carries no credential, no git configuration and no agent instruction file.
RUN rm -rf /root/.ssh /root/.gitconfig /home/node/.ssh /home/node/.gitconfig /etc/gitconfig
USER node
WORKDIR /work
