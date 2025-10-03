FROM python:3.12-alpine

LABEL version="1.0"
LABEL description="Test image for pytest and coverage"

WORKDIR /app

COPY requirements.txt .

RUN apk update && \
    apk add --no-cache --upgrade bash postgresql-client ffmpeg && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

COPY . .

RUN apk add --no-cache dos2unix bash && \
    find . -type f -name "*.sh" -exec dos2unix {} \; && \
    find . -type f -name "*.sh" -exec chmod +x {} \; && \
    apk del dos2unix

COPY scripts/wait-for-it.sh /app/scripts/wait-for-it.sh
RUN dos2unix /app/scripts/wait-for-it.sh && chmod +x /app/scripts/wait-for-it.sh

ENTRYPOINT ["/bin/sh", "/app/backend.test.entrypoint.sh"]