FROM python:3.8-slim-buster

# Select workdir
WORKDIR /usr/src/osm-detective

# Copy Source code
COPY . .

# Labels
LABEL maintainer = "dearrude@tfwno.gf"

# Install dependency
RUN pip install poetry
RUN apt-get update
RUN apt-get install -y libcurl4-openssl-dev libssl-dev gcc
RUN poetry install --no-dev

# Run scheduled
CMD [ "poetry", "run", "python3", "./src/main.py" ]
