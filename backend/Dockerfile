FROM python:3.10


WORKDIR /app
COPY ./requirements.txt requirements.txt

RUN pip install -r requirements.txt
RUN ln -sf /usr/share/zoneinfo/Europe/Madrid /etc/localtime

RUN echo "cd /app && pip install -r requirements" > /build_backend.sh

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]