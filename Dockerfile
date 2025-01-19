FROM python:3.13

WORKDIR /home/app
COPY . .
RUN pip install .

CMD [ "panel serve src/ebb_flow_manager/ebb_flow_manager_*" ]
