FROM python

COPY ./requirements.txt /data/requirements_app.txt
COPY ./testdata/requirements.txt /data/requirements_tests.txt


RUN pip install -r /data/requirements_app.txt
RUN pip install -r /data/requirements_tests.txt

COPY . /app
WORKDIR /app
EXPOSE 80

ENTRYPOINT ["/usr/local/bin/pytest", "-s", "-v"]