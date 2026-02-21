FROM python:3.12.12-slim AS builder

ARG DIR_NAME
ARG GROUPS

RUN pip install --no-cache-dir poetry==2.3.2
RUN poetry config virtualenvs.create false

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

RUN poetry install --only main,"${GROUPS}" --no-interaction --no-ansi --no-root

FROM python:3.12.12-slim
ARG DIR_NAME

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY service/${DIR_NAME}/ /app/service/${DIR_NAME}/
COPY service/tests/ /app/tests

EXPOSE 8000

RUN groupadd -g 1001 ${DIR_NAME} && \
    useradd -u 1001 -g 1001 -m ${DIR_NAME} && \
    chown -R 1001:1001 /app

USER 1001

CMD ["sh", "-c", "exec python -m service.${APP_DIR}.app"]
