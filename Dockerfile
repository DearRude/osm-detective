FROM python:3.8-slim-buster

# Select workdir
WORKDIR /usr/osm-detective

# Copy Source code
COPY . .

# Labels
LABEL maintainer = "dearrude@tfwno.gf"

# Python Path
ENV PYTHONPATH "${PYTHONPATH}:/usr/osm-detective"

# Install dependency
RUN pip install poetry
RUN poetry install --no-dev

# Run scheduled
CMD [ "poetry", "run", "python3", "./src/main.py" ]
