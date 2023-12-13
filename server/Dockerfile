# Use an official lightweight Python image.
FROM python:3.9-slim

# Install system dependencies and the fr_CA.UTF-8 locale
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libjpeg-dev \
    python3-dev \
    tzdata \
    locales \
    libcairo2-dev \
    pkg-config \
 && rm -rf /var/lib/apt/lists/* \
 && cp /usr/share/zoneinfo/America/Toronto /etc/localtime \
 && echo "America/Toronto" >  /etc/timezone \
 && sed -i -e 's/# fr_CA.UTF-8 UTF-8/fr_CA.UTF-8 UTF-8/' /etc/locale.gen \
 && dpkg-reconfigure --frontend=noninteractive locales \
 && update-locale LANG=fr_CA.UTF-8

# Set the locale to fr_CA.UTF-8
ENV TZ=America/Toronto
ENV LANG=fr_CA.UTF-8
ENV LANGUAGE=fr_CA:fr
ENV LC_ALL=fr_CA.UTF-8

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