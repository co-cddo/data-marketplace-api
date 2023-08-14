FROM python:3.11.4-alpine3.18

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./queries /code/queries

ENV USER=fastapi
ENV UID=12345
ENV GID=23456

RUN addgroup --gid "$GID" "$USER"
RUN adduser \
    --disabled-password \
    --gecos "" \
    --ingroup "$USER" \
    --no-create-home \
    --uid "$UID" \
    "$USER"

RUN chown -R "$USER":"$USER" /code/app

USER fastapi

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]