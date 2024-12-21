FROM python:3.13

WORKDIR /home/app
COPY . .
RUN pip install .

CMD [ "ebb_flow_manager" ]
