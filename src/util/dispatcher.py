import json

import requests as requests

from src.service.EventService import EventService
from src.util import serializer, logwrapper


# sends an update to the document service
def send_update_to_document_service(doc_id: str, user_id: str, entities: dict, sentence_entities: list,
                                    relations: dict):
    with open('./config.json', 'r') as f:
        config = json.load(f)

    doc_address = config['doc_address'] + '/api/v1/documents/' + doc_id
    data = {
        'userId': user_id,
        'entities': entities,
        'sentence_entities': sentence_entities,
        'relations': relations
    }
    requests.patch(doc_address, json=data)
    logwrapper.info(f'Send update to: {doc_address}')


# Send a training request to the ai service
def send_ai_training_request(req):
    with open('./config.json', 'r') as f:
        config = json.load(f)

    ai_address = config['ai_address'] + '/api/v1/train'
    requests.post(ai_address, json=req)

    logwrapper.info(f'Send train request to AI.')


def send_ai_prediction_request(req):
    with open('./config.json', 'r') as f:
        config = json.load(f)

    ai_address = config['ai_address'] + '/api/v1/pred'
    requests.post(ai_address, json=req)

    logwrapper.info(f'Send pred request to AI.')
