FROM python:3.13-alpine AS generate-venv

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN ["pip", "install", "pipenv"]
RUN ["sh", "-c", "pipenv requirements > requirements.txt"]
RUN ["python3", "-m", "venv", "/venv"]
ENV PATH="/venv/bin:$PATH"
RUN ["python3", "-m", "pip", "install", "-r", "requirements.txt"]

FROM python:3.13-alpine AS runtime
WORKDIR /app
COPY --from=generate-venv /venv /venv
ENV PATH="/venv/bin:$PATH"
COPY src ./src
COPY *.py ./
ENTRYPOINT ["python3", "run.py"]
CMD ["--automatic"]