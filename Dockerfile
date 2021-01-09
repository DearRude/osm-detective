FROM python:3.8-slim-buster

# Select workdir
WORKDIR /usr/src/osm-detective

# Copy requirements generated by poetry
COPY ./requirements.txt ./requirements.txt

# Labels
LABEL maintainer = "dearrude@tfwno.gf"

# Install dependency
RUN apt-get update && apt-get install -y libcurl4-openssl-dev libssl-dev gcc
RUN pip install -r requirements.txt

# Copy Source code
COPY . .

# Run scheduled
CMD [ "python3", "./src/main.py" ]
