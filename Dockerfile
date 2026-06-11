FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir flask werkzeug pyjwt python-dotenv numpy reportlab gunicorn flask-cors

COPY . .

ENV FLASK_ENV=production
ENV DATABASE_URL=sqlite:///ecotrace.db

EXPOSE 5000

CMD ["gunicorn", "run:app", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120"]
