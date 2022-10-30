import unittest
import os

from uuid import UUID

from src.service.EventService import EventService

class TestEventServie(unittest.TestCase):

    def test_create_project(self):
        service = EventService()

        projects = service.get_all_projects()
        self.assertEqual(len(projects), 0)

        service.create_project('name', 'date', 'creator', 'ca6733fa-d416-413c-80e9-ec00baeb2c74')
        project_id = service.create_project('name2', 'date2', 'creator2', 'aa6733fa-d416-413c-80e9-ec00baeb2c74')
        project_id = str(project_id)

        projects = service.get_all_projects()
        self.assertEqual(len(projects), 2)

        project = service.get_project(project_id)
        self.assertEqual(project.id, UUID(project_id))
        self.assertEqual(project.name, 'name2')
        self.assertEqual(project.creator, 'creator2')
        self.assertEqual(project.date, 'date2')
        self.assertEqual(project.labelSetId, UUID('aa6733fa-d416-413c-80e9-ec00baeb2c74'))
        self.assertEqual(project.documents, [])
        self.assertEqual(project.deleted, False)

        print('test_create_project finished.')


    def test_delete_project(self):
        service = EventService()

        project_id = service.create_project('name', 'date', 'creator', 'ca6733fa-d416-413c-80e9-ec00baeb2c74')
        project_id = str(project_id)

        projects = service.get_all_projects()
        self.assertEqual(len(projects), 1)

        service.delete_project(project_id)

        projects = service.get_all_projects()
        self.assertEqual(len(projects), 0)

        project = service.get_project(project_id)

        self.assertEqual(project.id, UUID(project_id))
        self.assertEqual(project.name, 'name')
        self.assertEqual(project.creator, 'creator')
        self.assertEqual(project.date, 'date')
        self.assertEqual(project.labelSetId, UUID('ca6733fa-d416-413c-80e9-ec00baeb2c74'))
        self.assertEqual(project.documents, [])
        self.assertEqual(project.deleted, True)

        print('test_delete_project finished.')

    def test_update_project(self):
        service = EventService()

        project_id = service.create_project('name', 'date', 'creator', 'ca6733fa-d416-413c-80e9-ec00baeb2c74')
        project_id = str(project_id)

        project = service.get_project(project_id)
        
        self.assertEqual(project.id, UUID(project_id))
        self.assertEqual(project.name, 'name')
        self.assertEqual(project.creator, 'creator')
        self.assertEqual(project.date, 'date')
        self.assertEqual(project.labelSetId, UUID('ca6733fa-d416-413c-80e9-ec00baeb2c74'))
        self.assertEqual(project.documents, [])

        service.update_project(project_id, 'name2', 'date2', 'creator2')
        
        project = service.get_project(project_id)

        self.assertEqual(project.id, UUID(project_id))
        self.assertEqual(project.name, 'name2')
        self.assertEqual(project.creator, 'creator2')
        self.assertEqual(project.date, 'date2')
        self.assertEqual(project.labelSetId, UUID('ca6733fa-d416-413c-80e9-ec00baeb2c74'))
        self.assertEqual(project.documents, [])

        print('test_update_project finished.')

    def test_add_remove_documents(self):

        service = EventService()

        project_id = service.create_project('name', 'date', 'creator', 'ca6733fa-d416-413c-80e9-ec00baeb2c74')
        project_id = str(project_id)

        project = service.get_project(project_id)
        self.assertEqual(project.documents, [])

        service.add_document(project_id, 'ca6733fa-d416-413c-80e9-ec00baeb2c11')
        service.add_document(project_id, 'ca6733fa-d416-413c-80e9-ec00baeb2c13')

        project = service.get_project(project_id)
        self.assertEqual(project.documents, [UUID('ca6733fa-d416-413c-80e9-ec00baeb2c11'), UUID('ca6733fa-d416-413c-80e9-ec00baeb2c13')])

        service.remove_document(project_id, 'ca6733fa-d416-413c-80e9-ec00baeb2c13')

        project = service.get_project(project_id)
        self.assertEqual(project.documents, [UUID('ca6733fa-d416-413c-80e9-ec00baeb2c11')])

        print('test_add_remove_documents finished.')

    # Test creating a document
    def test_create_document(self):
        service = EventService()

        doc_id = service.create_document()
        doc_id = str(doc_id)

        doc = service.get_document(doc_id)

        self.assertEqual(doc, {'id': doc_id, 'labels': [], 'relations': []})

if __name__ == '__main__':
    unittest.main()