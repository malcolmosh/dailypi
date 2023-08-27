# Use an official lightweight Python image.
FROM python:3.9-alpine

# Copy and install requirements
RUN apk update && apk add \
    gcc \
    g++ \
    freetype-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libjpeg \
    python3-dev 

# Codebase setup
RUN mkdir /app/
WORKDIR /app/

# Add all code
ENV PYTHONPATH /dispatchpi
ADD . /app/

# Install dependencies into this container so there's no need to 
# install anything at container run time.
RUN pip install -r requirements.txt --upgrade

# Service must listen to $PORT environment variable.
# This default value facilitates local development.
ENV PORT 8080

# Run the web service on container startup. Here you use the gunicorn
# server, with one worker process and 8 threads. For environments 
# with multiple CPU cores, increase the number of workers to match 
# the number of cores available.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 main:app