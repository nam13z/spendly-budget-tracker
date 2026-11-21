FROM node:26.13.1-bookworm-slim AS node-runtime

FROM python:3.14.10-slim-bookworm

COPY --from=node-runtime /usr/local/ /usr/local/

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates git passwd \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid vscode --create-home --shell /bin/bash vscode \
    && mkdir -p /workspaces/spendly-budget-tracker \
    && chown vscode:vscode /workspaces/spendly-budget-tracker \
    && test "$(python --version)" = "Python 3.14.10" \
    && test "$(node --version)" = "v26.13.1"

WORKDIR /workspaces/spendly-budget-tracker
USER vscode
