import json
import sys
from threading import Thread

from flask import Flask
from flask_restful import Api
from flask_cors import CORS

import pymongo
import os

from src.api.resources import Project, ProjectList, Document, DocumentList, EntitySetList, EnititySet, RelationSetList, RelationSet
from src.service.EventService import EventService
from src.util import logwrapper
from src.util.listener import listening_thread


def main():
    # read config
    if not os.path.exists('./config.json'):
        logwrapper.error('No Config File. Shutting down.')
        sys.exit()

    with open('./config.json', 'r') as f:
        config = json.load(f)

    # Event sourcing configuration.
    #os.environ["PERSISTENCE_MODULE"] = "eventsourcing.postgres"
    #os.environ['INFRASTRUCTURE_FACTORY'] = 'eventsourcing.postgres:Factory'
    #os.environ['POSTGRES_DBNAME'] = 'anno_events'
    #os.environ['POSTGRES_HOST'] = '127.0.0.1'
    #os.environ['POSTGRES_PORT'] = '27017'
    #os.environ['POSTGRES_USER'] = 'gnuma'
    #os.environ['POSTGRES_PASSWORD'] = 'gnuma'
    #os.environ['POSTGRES_CONN_MAX_AGE'] = '10'
    #os.environ['POSTGRES_PRE_PING'] = 'y'
    #os.environ['POSTGRES_LOCK_TIMEOUT'] = '5'
    #os.environ['POSTGRES_IDLE_IN_TRANSACTION_SESSION_TIMEOUT'] = '5'

    os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"
    os.environ["SQLITE_DBNAME"] = "./anno_db.sqlite"
    os.environ["SQLITE_LOCK_TIMEOUT"] = "10"


    # Set up Flask and the Rest API.
    app = Flask(__name__)
    api = Api(app)

    # Define CORS settings.
    cors = CORS(app, resources={
        r'/api/*': {
            'origins': '*'
        }
    })

    # Connect to MongoDB
    mongo_client = pymongo.MongoClient(config['mongo_db_address'])
    anno_db = mongo_client['anno_db']

    # Set up event sourcing service
    event_service = EventService()

    # Add resources to the API.
    pre = '/api/v1'
    api.add_resource(ProjectList, f'{pre}/projects', resource_class_kwargs={'event_service': event_service})
    api.add_resource(Project, f'{pre}/projects/<project_id>', resource_class_kwargs={'event_service': event_service})
    api.add_resource(DocumentList, f'{pre}/projects/<project_id>/docs', resource_class_kwargs={'event_service': event_service})
    api.add_resource(Document, f'{pre}/projects/<project_id>/docs/<doc_id>/user/<user_id>',
                     resource_class_kwargs={'event_service': event_service, 'anno_db': anno_db})
    api.add_resource(EntitySetList, f'{pre}/entities', resource_class_kwargs={'anno_db': anno_db})
    api.add_resource(EnititySet, f'{pre}/entities/<entity_id>', resource_class_kwargs={'anno_db': anno_db})
    api.add_resource(RelationSetList, f'{pre}/relations', resource_class_kwargs={'anno_db': anno_db})
    api.add_resource(RelationSet, f'{pre}/relations/<relation_id>', resource_class_kwargs={'anno_db': anno_db})

    # Start the thread listening to rabbbit mq
    t = Thread(target=listening_thread, args=(event_service, anno_db, config,))
    t.start()

    # Start the server.
    app.run(debug=False, port=config['port'], host='0.0.0.0')


if __name__ == '__main__':
    main()
