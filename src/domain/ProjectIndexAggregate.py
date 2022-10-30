from eventsourcing.domain import Aggregate, AggregateEvent, AggregateCreated

from typing import Set
from uuid import uuid5, NAMESPACE_URL, UUID

class ProjectIndexAggregate(Aggregate):

    def __init__(self):
        self.projects: Set[UUID] = set()

    @classmethod
    def create_id(cls):
        return uuid5(NAMESPACE_URL, f'/projects')

    @classmethod
    def get(cls):
        index_id = cls.create_id()
        return cls._create(cls.Created, id=index_id)

    def add_project_to_index(self, project_id):
        self.trigger_event(self.ProjectAddedEvent, project_id= project_id)

    def remove_project_from_index(self, project_id):
        self.trigger_event(self.ProjectRemovedEvent, project_id = project_id) 

    class Created(AggregateCreated):
        pass

    class ProjectAddedEvent(AggregateEvent):
        project_id: UUID

        def apply(self, index):
            assert isinstance(index, ProjectIndexAggregate)
            
            index.projects.add(self.project_id)

    class ProjectRemovedEvent(AggregateEvent):
        project_id: UUID

        def apply(self, index):
            assert isinstance(index, ProjectIndexAggregate)

            if self.project_id in index.projects:
                index.projects.remove(self.project_id)