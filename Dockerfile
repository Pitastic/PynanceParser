FROM ubuntu:24.04

RUN apt update && apt install python3.12-venv apache2 libapache2-mod-wsgi-py3 python3-pip -y

COPY . /app
WORKDIR /app

RUN /usr/bin/python3.12 -m venv .venv && \
    . .venv/bin/activate && \
    .venv/bin/python3 -m pip install --upgrade pip && \
    .venv/bin/python3 -m pip install -r requirements.txt

COPY apache2.conf /etc/apache2/sites-available/pynanceparser.conf
RUN a2ensite pynanceparser && a2dissite 000*
RUN ln -sf /dev/stdout /var/log/apache2/access.log && \
    ln -sf /dev/stdout /var/log/apache2/error.log

EXPOSE 80

ENTRYPOINT ["apachectl", "-D", "FOREGROUND"]
