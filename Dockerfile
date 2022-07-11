FROM    python:3.9-buster AS base
ENV     PYTHONUNBUFFERED=true \
        PATH=/root/.local/bin:${PATH}
WORKDIR /src
RUN     apt update && \
        curl -sSL https://install.python-poetry.org | python - --preview

FROM    base
ADD     . ./
RUN     poetry config virtualenvs.create false && \
        poetry install --only main
WORKDIR /src/service
CMD     exec uvicorn --host 0.0.0.0 --port $PORT main:app --factory
