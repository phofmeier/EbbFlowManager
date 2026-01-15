FROM python:3.13

WORKDIR /home/app
COPY . .
RUN pip install .

CMD [ "panel", "serve", "src/ebb_flow_manager/ebb_flow_manager_app.py", "src/ebb_flow_manager/ebb_flow_manager_templates.py", "src/ebb_flow_manager/ebb_flow_manager_data_viewer.py" ]
