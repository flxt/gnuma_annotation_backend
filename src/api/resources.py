from flask import request
from flask_restful import Resource, abort

import uuid

from src.util import logwrapper

from src.util.dispatcher import send_ai_training_request, send_update_to_document_service, send_ai_prediction_request
from src.util.serializer import serialize_project, serialize_document


# calculate ai stats
# could be moved to a utils file
def get_ai_stats(ent_preds, ent_golden, rel_preds, rel_golden):
    # no ai prediction, no ai stats
    if len(ent_golden) == 0 and len(rel_golden) == 0:
        return {
            'ner_f1': -1,
            'rel_f1': -1
        }

    # ent f1
    ent_tp = 0

    for _, pred in ent_preds.items():
        for _, golden in ent_golden.items():
            if (pred['sentenceIndex'] == golden['sentenceIndex'] and pred['type'] == golden['type'] and
                    pred['start'] == golden['start'] and pred['end'] == golden['end']):
                ent_tp +=1

    ent_fp = len(ent_preds) - ent_tp
    ent_fn = len(ent_golden) - ent_tp

    if ent_fp == 0 and ent_tp == 0 and ent_fn == 0:
        ent_f1_micro = 0
    else:
        ent_f1_micro = (2 * ent_tp) / (2 * ent_tp + ent_fp + ent_fn + 1e-6)

    # rel f1 with ner
    rel_tp = 0
    for _, pred in rel_preds.items():
        for _, golden in rel_golden.items():
            if (pred['type'] == golden['type'] and
                    ent_preds[pred['head']]['sentenceIndex'] == ent_golden[golden['head']]['sentenceIndex'] and
                    ent_preds[pred['head']]['start'] == ent_golden[golden['head']]['start'] and
                    ent_preds[pred['head']]['end'] == ent_golden[golden['head']]['end'] and
                    ent_preds[pred['head']]['type'] == ent_golden[golden['head']]['type'] and
                    ent_preds[pred['tail']]['sentenceIndex'] == ent_golden[golden['tail']]['sentenceIndex'] and
                    ent_preds[pred['tail']]['start'] == ent_golden[golden['tail']]['start'] and
                    ent_preds[pred['tail']]['end'] == ent_golden[golden['tail']]['end'] and
                    ent_preds[pred['tail']]['type'] == ent_golden[golden['tail']]['type']):
                rel_tp += 1

    rel_fp = len(rel_preds) - rel_tp
    rel_fn = len(rel_golden) - rel_tp

    if rel_fp == 0 and rel_tp == 0 and rel_fn == 0:
        rel_f1_micro = 0
    else:
        rel_f1_micro = (2 * rel_tp) / (2 * rel_tp + rel_fp + rel_fn + 1e-6)

    return {
        'ner_f1': ent_f1_micro * 100,
        'rel_f1': rel_f1_micro * 100
    }


# Get a list of projects or create a new project.
class ProjectList(Resource):

    # Init the resource.
    def __init__(self, event_service):
        self._event_service = event_service

    # Get a list of all existing projects.
    def get(self):
        return [serialize_project(pro) for pro in self._event_service.get_all_projects()]
    
    # Create a new project.
    def post(self):
        data = request.json

        new_id = self._event_service.create_project(data['name'], data['date'], data['creator'], data['labelSetId'], data['relationSetId'])
        logwrapper.info(f'Created new project with id {new_id}.')

        return str(new_id)

# Handle one specific project.
class Project(Resource):

    # Init the resource.
    def __init__(self, event_service):
        self._event_service = event_service

    # Delete a project.
    def delete(self, project_id):
        self._event_service.delete_project(project_id)

        return 200

    # Edit a project.
    def patch(self, project_id):
        data = request.json

        self._event_service.update_project(project_id, data['name'], data['creator'])

        return 200

    # Get project.
    def get(self, project_id):
        return (serialize_project(self._event_service.get_project(project_id)))


# Get a list of documents in a project.
class DocumentList(Resource):

    # Init the resource
    def __init__(self, event_service):
        self._event_service = event_service

    # Get a list of all documents in the project.
    def get(self, project_id):
        out = []
        project = self._event_service.get_project(project_id)

        for _id in project.documents:
            out.append({
                'id': str(_id),
                'labelled': project.labelled[_id],
                'labelledBy': project.labelled_by[_id],
                'aiStats': project.ai_stats[_id]
            })

        return out

    # Add a document to the project
    def post(self, project_id):
        data = request.json

        if uuid.UUID(data['docId']) not in self._event_service.get_project(project_id).documents:
            self._event_service.add_document(project_id, data['docId'])

            return data['docId']

        return 400

        # Remove a document from the project
    def delete(self, project_id):
        data = request.json

        self._event_service.remove_document(project_id, data['docId'])

        return 200


# Handle one document
class Document(Resource):

    # Init the resource
    def __init__(self, event_service, anno_db):
        self._event_service = event_service
        self._doc_register = anno_db['doc_register']
        self._label_set_col = anno_db['label_sets']
        self._relation_set_col = anno_db['relation_sets']

    # Get document labels and relations.
    def get(self, project_id, doc_id, user_id):
        project = self._event_service.get_project(project_id)

        if uuid.UUID(doc_id) not in project.documents:
            abort(400, message=f'Document {doc_id} not in project {project_id}')

        db_result = self._doc_register.find_one({
            'project_id': project_id,
            'doc_id': doc_id,
            'user_id': user_id
        })

        if(not db_result):
            new_id = self._event_service.create_document()
            self._doc_register.insert_one({
                'project_id': project_id,
                'doc_id': doc_id,
                'user_id': user_id,
                '_id': str(new_id),
                'id': str(new_id)
            })
        else:
            new_id = db_result['_id']

        doc = self._event_service.get_document(str(new_id))

        db_result = self._doc_register.find_one({'_id': str(new_id)})

        # serialize document
        serialized_doc = serialize_document(doc, db_result, project)

        return serialized_doc


    # post request for sending the document in for prediction
    # only done if document is not labelled
    # if labelled => set known labels from different annotator as recommendations
    def post (self, project_id, doc_id, user_id):
        project = self._event_service.get_project(project_id)

        if uuid.UUID(doc_id) not in project.documents:
            abort(400, message=f'No document with id {doc_id} in project {project_id}')

        db_result = self._doc_register.find_one({
            'project_id': project_id,
            'doc_id': doc_id,
            'user_id': user_id
        })

        if (not db_result):
            new_id = self._event_service.create_document()
            self._doc_register.insert_one({
                'project_id': project_id,
                'doc_id': doc_id,
                'user_id': user_id,
                '_id': str(new_id),
                'id': str(new_id)
            })
        else:
            new_id = db_result['_id']

        doc = self._event_service.get_document(str(new_id))

        # if no recommendation get some
        if (not user_id in project.labelled_by[uuid.UUID(doc_id)] and len(doc.orig_entity_preds) == 0 and
            len(doc.orig_relation_preds) == 0):

            # labelled => take user labels and recommend those
            if project.labelled[uuid.UUID(doc_id)]:
                # give recs
                self._event_service.set_document_rec(doc_id, doc.entities, doc.sentence_entities, doc.relations)

            # else ask ai for predictions
            else:
                # enitity types
                label_set = self._label_set_col.find_one({'_id': str(project.labelSetId)})
                labs = []
                for ele in label_set['labels']:
                    labs.append(ele['type'])

                # relation types
                relation_set = self._relation_set_col.find_one({'_id': str(project.relationSetId)})
                rels = []
                for ele in relation_set['relationTypes']:
                    rels.append(ele['type'])

                # send the train request
                req = {
                    'project_id': str(project_id),
                    'document_id': str(doc_id),
                    'entity_types': labs,
                    'relation_types': rels
                }

                send_ai_prediction_request(req)


    # Update Labels and Relations
    def patch(self, project_id, doc_id, user_id):
        project = self._event_service.get_project(project_id)

        if uuid.UUID(doc_id) not in project.documents:
            abort(400, message=f'No document with id {doc_id} in project {project_id}')

        data = request.json

        db_result = self._doc_register.find_one({
            'project_id': project_id,
            'doc_id': doc_id,
            'user_id': user_id
        })

        if not db_result:
            new_id = self._event_service.create_document()
            self._doc_register.insert_one({
                'project_id': project_id,
                'doc_id': doc_id,
                'user_id': user_id,
                '_id': str(new_id),
                'id': str(new_id)
            })
        else:
            new_id = db_result['_id']

        #todo do a proper check
        try:
            self._event_service.update_document(new_id, data['entities'], data['sentenceEntities'], data['relations'])
        except:
            pass

        try:
            self._event_service.update_document_rec(new_id, data['recEntities'], data['recSentenceEntities'],
                                                    data['recRelations'])
        except:
            pass

        # Mark document as labelled by user if labelled and send update to document service.
        # Send a train request to the ai service as well
        if 'labelled' in data and data['labelled']:
            doc = self._event_service.get_document(new_id)

            # calculate ai stats if first labelling and send train request
            if not project.labelled[uuid.UUID(doc_id)]:
                ai_stats = get_ai_stats(doc.orig_entity_preds, data['entities'], doc.orig_relation_preds,
                                        data['relations'])

                # send train request
                train_data = []
                test_data = []

                # fill data lists
                for pr_doc_id in project.documents:

                    # not labelled => test => gets predicted
                    if not project.labelled[pr_doc_id]:
                        test_data.append(str(pr_doc_id))
                    # else => train data
                    else:
                        lab_doc_result = self._doc_register.find_one({
                            'project_id': project_id,
                            'doc_id': str(pr_doc_id),
                            'user_id': project.labelled_by[pr_doc_id][0]
                        })
                        lab_doc = self._event_service.get_document(lab_doc_result['_id'])
                        train_data.append({
                            'doc_id': str(pr_doc_id),
                            'entities': lab_doc.entities,
                            'sentence_entities': lab_doc.sentence_entities,
                            'relations': lab_doc.relations
                        })

                # enitity types
                label_set = self._label_set_col.find_one({'_id': str(project.labelSetId)})
                labs = []
                for ele in label_set['labels']:
                    labs.append(ele['type'])

                # relation types
                relation_set = self._relation_set_col.find_one({'_id': str(project.relationSetId)})
                rels = []
                for ele in relation_set['relationTypes']:
                    rels.append(ele['type'])

                # send the train request
                req = {
                    'project_id': str(project_id),
                    'train_data': train_data,
                    'entity_types': labs,
                    'relation_types': rels

                }
                send_ai_training_request(req)
            else:
                ai_stats = project.ai_stats[uuid.UUID(doc_id)]

            # update document
            self._event_service.mark_document(project_id, doc_id, user_id, ai_stats)

            # send update to doc service
            send_update_to_document_service(doc_id, user_id, doc.entities, doc.sentence_entities, doc.relations)

        return 200


# Get a list of label sets or create a new one.
class EntitySetList(Resource):

    # Init the resource.
    def __init__(self, anno_db):
        self._label_set_col = anno_db['label_sets'] 

    # Get a list of all posible label sets.
    def get(self):
        label_sets = self._label_set_col.find()
        label_sets = list(label_sets)

        logwrapper.debug(f'Label sets: {label_sets}')

        return label_sets

    # Create a new label set
    def post(self):
        data = request.json

        new_id = str(uuid.uuid4())
        data['_id'] = new_id
        data['id'] = new_id

        self._label_set_col.insert_one(data)

        logwrapper.info(f'Inserted new label set with id {new_id}.')

        return new_id

# Get info for one label set.
class EnititySet(Resource):

    # Init the resource.
    def __init__(self, anno_db):
        self._label_set_col = anno_db['label_sets'] 

    def get (self, entity_id):
        label_set = self._label_set_col.find_one({'_id': entity_id})

        logwrapper.debug(f'id: {entity_id} - label set: {label_set}')

        if (not label_set):
            abort(400, messsage=f'No label set with id {entity_id} exists.')

        return label_set


# Get a list of relation sets or create a new one.
class RelationSetList(Resource):

    # Init the resource.
    def __init__(self, anno_db):
        self._relation_set_col = anno_db['relation_sets'] 

    # Get a list of all posible relation sets.
    def get(self):
        relation_sets = self._relation_set_col.find()
        relation_sets = list(relation_sets)

        logwrapper.debug(f'Relation sets: {relation_sets}')

        return relation_sets

    # Create a new relation set
    def post(self):
        data = request.json

        new_id = str(uuid.uuid4())
        data['_id'] = new_id
        data['id'] = new_id

        self._relation_set_col.insert_one(data)

        logwrapper.info(f'Inserted new relation set with id {new_id}.')

        return new_id

# Get info for one relation set.
class RelationSet(Resource):

    # Init the resource.
    def __init__(self, anno_db):
        self._relation_set_col = anno_db['relation_sets'] 

    def get (self, relation_id):
        relation_set = self._relation_set_col.find_one({'_id': relation_id})

        logwrapper.debug(f'id: {relation_id} - relation set: {relation_set}')

        if (not relation_set):
            abort(400, messsage=f'No relation set with id {relation_id} exists.')

        return relation_set