from eventsourcing.application import Application

from uuid import UUID, uuid4

from src.domain.ProjectAggregate import ProjectAggregate
from src.util import logwrapper


class ProjectApplication(Application):

    # Register a project.
    def create_project(self, name, date, creator, labelSetId, relationSetId):
        assert isinstance(name, str)
        assert isinstance(date, str)
        assert isinstance(creator, str)
        assert isinstance(labelSetId, UUID)

        project = ProjectAggregate(name = name, date = date, creator = creator, labelSetId = labelSetId, relationSetId = relationSetId)
        self.save(project)

        return project.id

    def update_project(self, project_id, name, creator):
        assert isinstance(project_id, UUID)
        assert isinstance(name, str)
        assert isinstance(creator, str)

        project = self.repository.get(project_id)
        project.update_metadata(name, creator)

        self.save(project)

    # Delete a project
    def delete_project(self, project_id):
        assert isinstance(project_id, UUID)

        project = self.repository.get(project_id)
        project.delete()

        self.save(project)

    # Add a document to the project.
    def add_document(self, project_id, doc_id):
        assert isinstance(project_id, UUID)
        assert isinstance(doc_id, UUID)

        project = self.repository.get(project_id)
        project.add_document(doc_id)

        self.save(project)

    # Remove a document from the project.
    def remove_document(self, project_id, doc_id):
        assert isinstance(project_id, UUID)
        assert isinstance(doc_id, UUID)

        project = self.repository.get(project_id)
        project.remove_document(doc_id)

        self.save(project)

    # Get the project.
    def get_project(self, project_id):
        assert isinstance(project_id, UUID)

        return self.repository.get(project_id)

    # Mark Document as labelled
    def mark_document(self, project_id, doc_id, user_id, ai_stats):
        assert isinstance(project_id, UUID)
        assert isinstance(doc_id, UUID)
        assert isinstance(user_id, str)
        assert isinstance(ai_stats, dict)

        project = self.repository.get(project_id)
        project.mark_document(doc_id, user_id, ai_stats)

        self.save(project)


    #Document not labelled any more
    def unmark_document(self, project_id, doc_id):
        assert isinstance(project_id, UUID)
        assert isinstance(doc_id, UUID)

        project = self.repository.get(project_id)
        project.unmark_document(doc_id)

        self.save(project)


