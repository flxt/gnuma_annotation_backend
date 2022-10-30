import json

import pika
import uuid

from src.service.EventService import EventService
from src.util import logwrapper


# thread to listening to rabbit mq
def listening_thread(event_service: EventService, mongo_db, config):
    rabbit_creds = config['rabbit_creds']

    # define connection parameters
    creds = pika.PlainCredentials(rabbit_creds['user'], rabbit_creds['pw'])
    params = pika.ConnectionParameters(host=rabbit_creds['host'], port=rabbit_creds['port'], credentials=creds)

    exchange = rabbit_creds['exchange']

    # init connection and channel
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # create exchange
    channel.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)

    # define and bind que
    result = channel.queue_declare(queue='', exclusive=True)

    queue_name = result.method.queue
    channel.queue_bind(exchange=exchange, queue=queue_name)

    # defines the callback method for the basic consume
    def backend_callback(ch, method, properties, body):
        logwrapper.info(f'ch -> {ch}')
        logwrapper.info(f'method -> {method}')
        logwrapper.info(f'properties -> {properties}')

        body = json.loads(body)

        # check if header has type
        if 'type' in properties.headers:
            # check for possible types
            if properties.headers['type'] == 'ai_update':
                assert isinstance(body['project_id'], str)
                assert isinstance(body['document_id'], str)
                assert isinstance(body['recEntities'], dict)
                assert isinstance(body['recSentenceEntities'], list)
                assert isinstance(body['recRelations'], dict)

                query = {'doc_id': body['document_id'], 'project_id': body['project_id']}
                results = mongo_db['doc_register'].find(query)

                for ele in results:
                    # update recs if not labelled. check if predictions already exist in doc aggregate
                    if not event_service.get_project(body['project_id']).labelled[uuid.UUID(body['document_id'])]:
                        event_service.set_document_rec(ele['_id'], body['recEntities'], body['recSentenceEntities'],
                                                       body['recRelations'])

                logwrapper.info(f'Received updated recommendations for document {body["document_id"]} in project '
                                f'{body["project_id"]}')

            elif properties.headers['type'] == 'document_deleted':
                if 'document_ids' in body:
                    assert isinstance(body['document_ids'], list)

                    for project in event_service.get_all_projects():
                        for doc_id in body['document_ids']:
                            doc_uuid = uuid.UUID(doc_id)
                            if doc_uuid in project.documents:
                                logwrapper.info(f'Removing document {doc_id} from project {str(project.id)}')
                                event_service.remove_document(str(project.id), doc_id)

            elif properties.headers['type'] == 'document_modified':
                if 'document_ids' in body:
                    assert isinstance(body['document_ids'], list)

                    for doc_id in body['document_ids']:
                        query = {'doc_id': doc_id}
                        results = mongo_db['doc_register'].find(query)

                        # clear docuemnts labels and unmark docs in project
                        for ele in results:
                            logwrapper.info(f'Clearing labels from user {ele["user_id"]} from document {ele["doc_id"]} '
                                            f'in project {ele["project_id"]}')
                            event_service.reset_document(ele['_id'])
                            event_service.unmark_document(ele['project_id'], ele['doc_id'])

    channel.basic_consume(queue=queue_name, on_message_callback=backend_callback, auto_ack=True)
    logwrapper.info(f'Start consuming for que {queue_name} on exchange {exchange}')

    try:
        channel.start_consuming()
    except (KeyboardInterrupt, SystemExit):
        print('Shutting down listening thread.')
