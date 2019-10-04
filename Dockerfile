FROM python:3.7.4

RUN mkdir -p /home/uploads
RUN mkdir -p /home/sports_classifier_app

WORKDIR /home/sports_classifier_app

COPY requirements.txt /home/sports_classifier_app/

RUN apt-get update -y && \
    apt install dumb-init && \
    pip install -r /home/sports_classifier_app/requirements.txt

COPY . /home/sports_classifier_app/.

EXPOSE 8080

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["/usr/local/bin/gunicorn", "-w", "2", "--bind", "0.0.0.0:8080", "wsgi:app" ,"--timeout", "300"]
