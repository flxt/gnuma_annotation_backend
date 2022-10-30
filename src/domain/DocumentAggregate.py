from eventsourcing.domain import Aggregate, event

from uuid import UUID

class DocumentAggregate(Aggregate):

    # Init a document.
    @event('Created')
    def __init__(self):
        self.entities = {}
        self.sentence_entities = []
        self.relations = {}
        self.rec_entities = {}
        self.rec_sentence_entities = []
        self.rec_relations = {}
        self.orig_entity_preds = {}
        self.orig_relation_preds = {}

    # Update relations and labels for user.
    def update(self, entities, sentence_entities, relations):
        assert isinstance(entities, dict)
        assert isinstance(sentence_entities, list)
        assert isinstance(relations, dict)

        self._update(entities, sentence_entities, relations)

    @event('UpdatedDocument')
    def _update(self, entities, sentence_entities, relations):
        self.entities = entities
        self.sentence_entities = sentence_entities
        self.relations = relations

    # update recommendations for doc
    def update_rec(self, rec_entities, rec_sentence_entities, rec_relations):
        assert isinstance(rec_entities, dict)
        assert isinstance(rec_sentence_entities, list)
        assert isinstance(rec_relations, dict)

        self._update_rec(rec_entities, rec_sentence_entities, rec_relations)

    @event('UpdatedDocumentRecommendations')
    def _update_rec(self, rec_entities, rec_sentence_entities, rec_relations):
        self.rec_entities = rec_entities
        self.rec_sentence_entities = rec_sentence_entities
        self.rec_relations = rec_relations

    # set recommendations for docuemnets aka first update
    def set_rec(self, rec_entities, rec_sentence_entities, rec_relations):
        assert isinstance(rec_entities, dict)
        assert isinstance(rec_sentence_entities, list)
        assert isinstance(rec_relations, dict)

        if len(self.orig_entity_preds) == 0 and len(self.orig_relation_preds) == 0:
            self._set_rec(rec_entities, rec_sentence_entities, rec_relations)

    @event('SetDocumentRecommendations')
    def _set_rec(self, rec_entities, rec_sentence_entities, rec_relations):
        self.rec_entities = rec_entities
        self.rec_sentence_entities = rec_sentence_entities
        self.rec_relations = rec_relations
        self.orig_entity_preds = rec_entities
        self.orig_relation_preds = rec_relations
