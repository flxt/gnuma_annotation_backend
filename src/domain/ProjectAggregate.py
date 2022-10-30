from eventsourcing.domain import Aggregate, event

from uuid import UUID

class ProjectAggregate(Aggregate):

    # Init a new project.
    @event('Created')
    def __init__(self, name, date, creator, labelSetId, relationSetId):
        assert isinstance(name, str)
        assert isinstance(date, str)
        assert isinstance(creator, str)
        assert isinstance(labelSetId, UUID)
        assert isinstance(relationSetId, UUID)

        self.documents = []
        self.labelled = {}
        self.labelled_by = {}
        self.ai_stats = {}
        self.deleted = False
        self.name = name
        self.date = date  
        self.creator = creator 
        self.labelSetId = labelSetId
        self.relationSetId = relationSetId

    # Remove a project.
    @event('Deleted')
    def delete(self):
        self.deleted = True

    def update_metadata(self, name, creator):
        assert isinstance(name, str)
        assert isinstance(creator, str)

        self._update_metadata(name, creator)

    @event('Updated')
    def _update_metadata(self, name, creator):
        self.name = name
        self.creator = creator 

    # Add mulitple documents to the list.
    def add_document(self, doc_id):
        assert isinstance(doc_id, UUID)

        self._add_document(doc_id)

    # Add single document to the list
    @event('DocumentAdded')
    def _add_document(self, doc_id):
        self.documents.append(doc_id)
        self.labelled[doc_id] = False
        self.labelled_by[doc_id] = []
        self.ai_stats[doc_id] = {
            'ner_f1': -1,
            'rel_f1': -1
        }

    # Remove a document from the list
    def remove_document(self, doc_id):
        assert isinstance(doc_id, UUID)

        self._delete_document(doc_id)

    @event('DocumentRemoved')
    def _delete_document(self, doc_id):
        self.documents.remove(doc_id)

    # Mark a document as labelled
    def mark_document(self, doc_id, user_id, ai_stats):
        assert isinstance(user_id, str)
        assert isinstance(doc_id, UUID)
        assert isinstance(ai_stats, dict)

        if user_id not in self.labelled_by[doc_id]:
            self._mark_document(doc_id, user_id, ai_stats)

    @event('DocumentMarked')
    def _mark_document(self, doc_id, user_id, ai_stats):
        self.labelled[doc_id] = True
        if user_id not in self.labelled_by[doc_id]:
            self.labelled_by[doc_id].append(user_id)
            self.ai_stats[doc_id] = ai_stats

    # Unlabel doc
    def unmark_document(self, doc_id):
        assert isinstance(doc_id, UUID)

        if doc_id in self.labelled:
            self._unmark_document(doc_id)

    @event('DocumentUnmarked')
    def _unmark_document(self, doc_id):
        self.labelled[doc_id] = False
        self.labelled_by[doc_id] = []
        self.ai_stats[doc_id] = {
            'ner_f1': -1,
            'rel_f1': -1
        }

