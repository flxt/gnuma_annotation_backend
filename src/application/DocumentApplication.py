from eventsourcing.application import Application

from uuid import UUID

from src.domain.DocumentAggregate import DocumentAggregate
from src.util import logwrapper

class DocumentApplication(Application):

    # Register a document.
    def create_document(self):
        doc = DocumentAggregate()
        self.save(doc)

        print(self.repository)

        return doc.id

    # Update entities and relations for the document.
    def update(self, doc_id, entities, sentence_entities, relations):
        assert isinstance(doc_id, UUID)

        doc = self.repository.get(doc_id)
        doc.update(entities, sentence_entities, relations)

        self.save(doc)

    # Update recommended enitities and relations for the document.
    def update_rec(self, doc_id, rec_entities, rec_sentence_entities, rec_relations):
        assert isinstance(doc_id, UUID)

        doc = self.repository.get(doc_id)
        doc.update_rec(rec_entities, rec_sentence_entities, rec_relations)

        self.save(doc)

    # Set recommended enitities and relations for the document.
    def set_rec(self, doc_id, rec_entities, rec_sentence_entities, rec_relations):
        assert isinstance(doc_id, UUID)

        doc = self.repository.get(doc_id)
        doc.set_rec(rec_entities, rec_sentence_entities, rec_relations)

        self.save(doc)

    # Get a document
    def get(self, doc_id):
        assert isinstance(doc_id, UUID)

        print(self.repository)

        return self.repository.get(doc_id)