FROM ubuntu:24.04

RUN apt update && apt install python3.12-venv apache2 libapache2-mod-wsgi-py3 -y

COPY . /app
WORKDIR /app
RUN /usr/bin/python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

COPY apache2.conf /etc/apache2/sites-available/pynanceparser.conf
RUN a2ensite pynanceparser && a2dissite 000-default.conf

EXPOSE 80
ENTRYPOINT ["apachectl", "-D", "FOREGROUND"]
