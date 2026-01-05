FROM ubuntu:24.04

RUN apt update && apt install python3.12-venv apache2 apache2-utils libapache2-mod-wsgi-py3 python3-pip -y

COPY . /app
WORKDIR /app

RUN /usr/bin/python3.12 -m venv .venv
RUN . .venv/bin/activate && \
    .venv/bin/python3.12 -m pip install --upgrade pip && \
    .venv/bin/python3.12 -m pip install -r requirements.txt

RUN sed -i -E s"|(DATABASE_BACKEND = )('tiny').*$|\1'mongo'|" app/config.py
RUN sed -i -E s"|(DATABASE_URI = )('/tmp').*$|\1'mongodb://mongo:27017'|" app/config.py
RUN sed -i -E s"|(DATABASE_NAME = )('testdata.json').*$|\1'pynanceparser'|" app/config.py

RUN cp docker/apache2.conf /etc/apache2/sites-available/pynanceparser.conf
RUN a2ensite pynanceparser && a2dissite 000*
RUN ln -sf /dev/stdout /var/log/apache2/access.log && \
    ln -sf /dev/stdout /var/log/apache2/error.log

EXPOSE 80

ENTRYPOINT ["/app/docker/entrypoint.sh"]
