from uuid import UUID

from src.service.EventService import EventService


def serialize_project(project):
    return {
        'id': str(project.id),
        'name': project.name,
        'date': project.date,
        'creator': project.creator,
        'labelSetId': str(project.labelSetId),
        'relationSetId': str(project.relationSetId),
        'documents': [str(doc_id) for doc_id in project.documents]
    }


def serialize_document(document, doc_info, project):
    return {
        'id': str(doc_info['doc_id']),
        'projectId': str(doc_info['project_id']),
        'userId': str(doc_info['user_id']),
        'entities': document.entities,
        'sentenceEntities': document.sentence_entities,
        'relations': document.relations,
        'labelled': project.labelled[UUID(doc_info['doc_id'])],
        'labelledBy': project.labelled_by[UUID(doc_info['doc_id'])],
        'recEntities': document.rec_entities,
        'recSentenceEntities': document.rec_sentence_entities,
        'recRelations': document.rec_relations,
        'aiStats': project.ai_stats[UUID(doc_info['doc_id'])]
    }
