FROM python:3.10-slim

# Install compilation dependencies
# lightfm needs gcc to build with OpenMP support if wheel is not perfect, though many linux wheels have it.
# We include build-essential just in case.
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
# Using pip directly for simplicity in Docker. 
# joblib, lightfm, numpy, pandas, scipy, psycopg2, dotenv
RUN pip install "numpy<2" pandas scipy scikit-learn lightfm joblib psycopg2-binary python-dotenv

# Copy training and evaluation scripts
COPY movies/ .
COPY songs/ .

# We expect the dataset to be mounted at /dataset and models at /models
# This will be handled by the docker run command

# Default command
CMD ["python", "movie_training.py"]
