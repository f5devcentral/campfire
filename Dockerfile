FROM python:3.6.6-alpine3.7

RUN apk update && apk add --no-cache bash curl python pkgconfig python-dev openssl-dev libffi-dev musl-dev make gcc linux-headers openssl \
    build-base cairo-dev cairo cairo-tools \
    # pillow dependencies
    jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev

RUN apk update && apk add gcc g++ make git patch perl perl-dev curl wget
RUN curl -L http://xrl.us/cpanm > /bin/cpanm && chmod +x /bin/cpanm
RUN cpanm App::cpm

RUN pip install "flask==1.0.1" "CairoSVG==2.1.3"

WORKDIR /usr
RUN cpm install Plack

ENV PERL5LIB=/usr/local/lib/perl5
ENV PATH=/usr/local/bin:$PATH


COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir /app

COPY src/ /app
COPY key.pem /app
COPY cert.pem /app

WORKDIR /app

EXPOSE 5002

ENV FLASK_ENV development
ENV HOME /app

ENTRYPOINT python app.py

