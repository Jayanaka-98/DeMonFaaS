ARG PYTHON_VERSION=3.8
FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/of-watchdog:0.10.4 AS watchdog
FROM --platform=${TARGETPLATFORM:-linux/amd64} python:${PYTHON_VERSION}-alpine AS build

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog


# Packages required for psycopg2
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

# Ruby sass
RUN apk add make ruby-dev
RUN gem install sass

#MAINTANER Your Name "youremail@domain.tld"
ENV MAIL_USERNAME=yourmail@test.com
ENV MAIL_PASSWORD=testpass
ENV SECRET_KEY=SuperRandomStringToBeUsedForEncryption
# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip3 install -r requirements.txt
ENV PYTHONIOENCODING=UTF-8
RUN pip3 install sqlalchemy_utils==0.38.3 flask_dance==5.1.0 Flask-Caching==1.11.1 python-gitlab==3.10.0

COPY . /app

#RUN python3 manage.py recreate_db && python3 manage.py setup_dev && python3 manage.py add_fake_data
ENV fprocess="python -u manage.py runserver"
ENV cgi_headers="true"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:5000"

# ENTRYPOINT ["python3", "-u" ,"manage.py", "runserver"]
HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]
