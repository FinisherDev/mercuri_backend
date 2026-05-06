ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

ENV SECRET_KEY "hUNqxdMWQNbrcquYicsD5U6upgM9Kn9jdmFJGJreUg1Ba6fXch"
ENV DB_NAME "dummy"
ENV DB_USER "dummy"
ENV DB_PASS "dummy"
ENV DB_HOST "dummy"
ENV DB_PORT "5432"
ENV FIREBASE_CREDENTIALS ""
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["daphne","-b","0.0.0.0","-p","8000","mercuri.asgi"]

