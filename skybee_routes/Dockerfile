# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# The port the container will listen on
EXPOSE 8000

# The command to run your application using Gunicorn
# This tells Gunicorn to run the 'application' object found in the 'skybee_routes/wsgi.py' file
CMD ["gunicorn", "skybee_routes.wsgi:application", "--bind", "0.0.0.0:8000"]