FROM python:3.13-slim

WORKDIR /

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /
RUN pip install uv
RUN uv sync --locked

COPY . .

CMD ["uv", "run", "python", "-m", "app.main"]
