#native libraries
import os
import time
import random

import datadog
dd_options = {
    'statsd_host' : os.environ['DD_AGENT_SERVICE_HOST'],
    'statsd_port' : os.environ['DD_AGENT_STATSD_PORT']
}
datadog.initialize(dd_options)


#flask stuff
from flask import Flask
import blinker as _

#trace stuff
from ddtrace import tracer, patch, Pin
from ddtrace.contrib.flask import TraceMiddleware

tracer.configure(
    hostname=os.environ['DD_AGENT_SERVICE_HOST'],
    port=os.environ['DD_AGENT_SERVICE_PORT'],
)

patch(sqlalchemy=True)

#postgres libraries
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select

app = Flask(__name__)

#patch traceware
traced_app = TraceMiddleware(app, tracer, service="my-flask-app", distributed_tracing=False)


#postgres stuff
POSTGRES = {
    'user': 'flask',
    'pw': 'flask',
    'db': 'docker',
    'host': os.environ['POSTGRES_SERVICE_HOST'],
    'port': os.environ['POSTGRES_SERVICE_PORT'],
}
pg_url = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
con = sqlalchemy.create_engine(pg_url, client_encoding='utf8')
meta = sqlalchemy.MetaData(bind=con, reflect=True)

web_origins = Table('web_origins', meta, autoload=True)

#logging stuff
import logging
import json_log_formatter
import threading

formatter = json_log_formatter.JSONFormatter()
json_handler = logging.FileHandler(filename='/var/log/mylog.json')
json_handler.setFormatter(formatter)
logger = logging.getLogger('my_json')
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

#routes

@app.route('/')
def hello_world():
    datadog.statsd.increment('counter_metric',tags=['endpoint:hello_world'])
    my_thread= threading.currentThread().getName()
    time.sleep(0.01)
    logger.info('hello_world has been executed', 
        extra={
            'job_category': 'hello_world', 
            'logger.name': 'my_json', 
            'logger.thread_name' : my_thread
        }
    )
    time.sleep(random.random()* 2)
    return 'Flask has been kuberneted \n'

@app.route('/bad')
def bad():
    datadog.statsd.increment('counter_metric',tags=['endpoint:bad'])

    my_thread= threading.currentThread().getName()
    time.sleep(0.01)
    logger.info('hello_world has been executed', 
        extra={
            'job_category': 'hello_world', 
            'logger.name': 'my_json', 
            'logger.thread_name' : my_thread
        }
    )
    time.sleep(random.random()* 2)
    return 'Flask has been kuberneted \n'.format(g)

@app.route('/query')
def return_results():
    datadog.statsd.increment('counter_metric',tags=['endpoint:query'])
    with tracer.trace("Random wait", service="my-flask-app") as span:
        my_thread= threading.currentThread().getName()
        time.sleep(0.01)
        logger.info('some postgres query has been made', 
            extra={
                'job_category': 'query', 
                'logger.name': 'my_json', 
                'logger.thread_name' : my_thread
            }
        )
        time.sleep(random.random()*1.5)
    with tracer.trace("database query", service="my-flask-app") as span:
        span.set_tag('sample','tag')
        conn = con.connect()
        s = select([web_origins])
        result = conn.execute(s)
        row = result.fetchone()
        conn.close()
        Pin.override(con, service='replica-db')
        return str(row) + '\n'
	
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')