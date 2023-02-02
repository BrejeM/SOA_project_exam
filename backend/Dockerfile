FROM ubuntu:latest

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

RUN apt-get update
RUN apt-get install -y python3 python3-pip vim

RUN mkdir /logs
RUN touch /logs/backend.log
RUN chmod 777 /logs/backend.log

COPY ./reqs.txt /reqs.txt
COPY ./backend.py /app.py


RUN pip install -r /reqs.txt

CMD ["/bin/python3", "/app.py"]
