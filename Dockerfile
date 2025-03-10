FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /TRE-LOGISTICA-2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project files
COPY . .

# Expose the default Django port
EXPOSE 8000

# Command to start the application
CMD python manage.py makemigrations && python manage.py migrate && gunicorn TRE-LOGISTICA-2.wsgi:application --bind 0.0.0.0:8000
