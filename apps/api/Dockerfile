FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PRFFS_ROOT_DIR=/app \
    PORT=8080

WORKDIR /app
COPY apps/api/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock

# The root .dockerignore includes the API and league assets, excluding secrets,
# local databases, frontend dependencies, and legacy Python scripts.
COPY . /app
RUN pip install --no-cache-dir --no-deps /app/apps/api \
    && useradd --uid 10001 --create-home prffs

USER prffs
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn prffs_api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
