from eventsourcing.application import AggregateNotFound
from eventsourcing.system import ProcessApplication
from eventsourcing.dispatch import singledispatchmethod

from uuid import UUID

from src.domain.ProjectAggregate import ProjectAggregate
from src.domain.ProjectIndexAggregate import ProjectIndexAggregate

class ProjectIndexProcessApplication(ProcessApplication):
    @singledispatchmethod
    def policy(self, domain_event, process_event):
        pass

    @policy.register(ProjectAggregate.Created)
    def _add_project_to_index(self, domain_event, process_event):
        assert isinstance(domain_event, ProjectAggregate.Created)

        index_id = ProjectIndexAggregate.create_id()
        try:
            index = self.repository.get(index_id)
        except AggregateNotFound:
            index = ProjectIndexAggregate.get()

        index.add_project_to_index(domain_event.originator_id)
        process_event.save(index)

    @policy.register(ProjectAggregate.Deleted)
    def _remove_project_from_index(self, domain_event, process_event):
        assert isinstance(domain_event, ProjectAggregate.Deleted)

        index_id = ProjectIndexAggregate.create_id()
        try:
            index = self.repository.get(index_id)
        except AggregateNotFound:
            index = ProjectIndexAggregate.get()

        index.remove_project_from_index(domain_event.originator_id)
        process_event.save(index)

    def create_index(self):
        index = ProjectIndexAggregate.get()
        self.save(index)
        return index.id

    def get_index(self, index_id):
        assert isinstance(index_id, UUID)

        return self.repository.get(index_id)

    def get_all_project_ids(self):
        index_id = ProjectIndexAggregate.create_id()
        try:
            index = self.repository.get(index_id)
            return list(index.projects)
        except AggregateNotFound:
            return []