from eventsourcing.system import SingleThreadedRunner, System

from uuid import UUID

from src.application.ProjectApplication import ProjectApplication
from src.application.ProjectIndexProcessApplication import ProjectIndexProcessApplication
from src.application.DocumentApplication import DocumentApplication
from src.util import logwrapper

class EventService:

    def __init__(self):
        logwrapper.info(f'Initializing EventService[{hex(id(self))}]...')

        self._system = System(pipes = [
            [ProjectApplication, ProjectIndexProcessApplication],
            [DocumentApplication]
        ])
        self._runner = SingleThreadedRunner(self._system)
        self._runner.start()

    def shutdown(self):
        logwrapper.info(f'Shutting down EventService[{hex(id(self))}]...')
        self._runner.stop()

    # Get a project
    def get_project(self, project_id: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Loading project {project_id}.')

        project_id = UUID(project_id)
        projects = self._runner.get(ProjectApplication)

        return projects.get_project(project_id)

    # Get all projects
    def get_all_projects(self):
        logwrapper.info(f'EventService[{hex(id(self))}]: Loading all projects.')

        indices = self._runner.get(ProjectIndexProcessApplication)
        projects = self._runner.get(ProjectApplication)

        project_ids = indices.get_all_project_ids()
        return [projects.get_project(project_id) for project_id in project_ids]

    # Create a project
    def create_project(self, name: str, date: str, creator: str, labelSetId: str, relationSetId: str):
        projects = self._runner.get(ProjectApplication)
        project_id = projects.create_project(name, date, creator, UUID(labelSetId), UUID(relationSetId))

        logwrapper.info(f'EventService[{hex(id(self))}]: Creating project {project_id}.')
        return (project_id)

    # Delete a project
    def delete_project(self, project_id: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Deleting project {project_id}.')

        projects = self._runner.get(ProjectApplication)
        projects.delete_project(UUID(project_id))

    # Update a project
    def update_project(self, project_id: str, name: str, creator: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Update project {project_id}.')

        projects = self._runner.get(ProjectApplication)
        projects.update_project(UUID(project_id), name, creator)

    # Add documents to project
    def add_document(self, project_id: str, doc_id: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Adding document {doc_id} to project {project_id}.')

        projects = self._runner.get(ProjectApplication)
        projects.add_document(UUID(project_id), UUID(doc_id))

    # Remove a document from the project
    def remove_document(self, project_id: str, doc_id: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Removing document {doc_id} from project {project_id}.')

        projects = self._runner.get(ProjectApplication)
        projects.remove_document(UUID(project_id), UUID(doc_id))

    # Mark document as labelled
    def mark_document(self, project_id: str, doc_id: str, user_id: str, ai_stats: dict):
        logwrapper.info(f'EventService[{hex(id(self))}]: Marking document {doc_id} from project {project_id} as labelled by user {user_id}.')

        projects = self._runner.get(ProjectApplication)
        projects.mark_document(UUID(project_id), UUID(doc_id), user_id, ai_stats)

    # UNMark document => not labelled
    def unmark_document(self, project_id: str, doc_id: str,):
        logwrapper.info(
            f'EventService[{hex(id(self))}]: Unmarking document {doc_id} from project {project_id}.')

        projects = self._runner.get(ProjectApplication)
        projects.unmark_document(UUID(project_id), UUID(doc_id))

    # Create a document.
    # In this case a document saves labels and relations
    # for one document, in one project for one specific user.
    def create_document(self):
        documents = DocumentApplication()
        doc_id = documents.create_document()

        logwrapper.info(f'EventService[{hex(id(self))}]: Creating document {doc_id}.')
        return doc_id

    # Update Labels and Relations for a document
    def update_document(self, doc_id: str, entities, sentence_entities, relations):
        logwrapper.info(f'EventService[{hex(id(self))}]: Updating document {doc_id}.')

        documents = DocumentApplication()
        documents.update(UUID(doc_id), entities, sentence_entities, relations)

    # Update recommended entities and Relations for a document
    def update_document_rec(self, doc_id: str, rec_entities, rec_sentence_entities, rec_relations):
        logwrapper.info(f'EventService[{hex(id(self))}]: Updating recommendations for document {doc_id}.')

        documents = DocumentApplication()
        documents.update_rec(UUID(doc_id), rec_entities, rec_sentence_entities, rec_relations)

    # Set recommended entities and Relations for a document
    def set_document_rec(self, doc_id: str, rec_entities, rec_sentence_entities, rec_relations):
        logwrapper.info(f'EventService[{hex(id(self))}]: Setting recommendations for document {doc_id}.')

        documents = DocumentApplication()
        documents.set_rec(UUID(doc_id), rec_entities, rec_sentence_entities, rec_relations)

    # Reset labels for a document.
    def reset_document(self, doc_id: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Reseting document {doc_id}.')

        documents = DocumentApplication()
        documents.update(UUID(doc_id), {}, [], {})
        documents.update_rec(UUID(doc_id), {}, [], {})

    # Get one document
    def get_document(self, doc_id: str):
        logwrapper.info(f'EventService[{hex(id(self))}]: Loading document {doc_id}.')

        doc_id = UUID(doc_id)
        documents = DocumentApplication()

        return documents.get(doc_id)