#!/usr/bin/env python
from flask_cloudant.error import FlaskCloudantException
from requests.exceptions import HTTPError
from cloudant.error import CloudantClientException

try:
    import cloudant
except ImportError:
    raise FlaskCloudantException(101)

__all__ = ('FlaskCloudant', )
__version__ = '0.0.1.dev'


class FlaskCloudant(object):
    """
    Creates a connection to CoudcDB server. Needs a `config.py` file
    with the `COUCH_USER`, `COUCH_PWD` and `COUCH_DB`.

    :param str app: Flask app initialized with `Flask(__name__)`.
    """

    CLIENT = None

    def __init__(self, app=None, **kwargs):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes the connection using the settings from `config.py`.
        """
        couch_user = app.config.get('COUCH_USER')
        couch_pwd = app.config.get('COUCH_PWD')
        couch_db = app.config.get('COUCH_DB')
        couch_url = app.config.get('COUCH_URL')

        try:
            FlaskCloudant.CLIENT = cloudant.CouchDB(couch_user, couch_pwd,
                                                     url=couch_url)
            self.__connect__()
            self._db = FlaskCloudant.CLIENT[couch_db]
            self.__disconnect__()
        except CloudantClientException as ex:
            raise FlaskCloudantException(ex.status_code)
        except HTTPError as ex:
            raise FlaskCloudantException(ex.response.status_code,
                                         couch_user)
        except KeyError:
            raise FlaskCloudantException(400, couch_db)

    def get(self, document_id):
        """
        Pulls a document from the database using the `document_id`.

        :param str document_id: Document ID used on the database.
        :returns: A `FlaskCloudantDocument` object.
        """
        self.__connect__()
        doc = FlaskCloudantDocument(cloudant.document.Document(self._db,
                                                               document_id))
        self.__disconnect__()
        return doc

    def put(self, content, document_id=None, override=False):
        """
        Creates a document on the database using the
        dictionary passed as paramenter.

        :param dict content: The content of your document.
        :param str document_id: _id for your document.
            Default: None. Cloudant will generate its own _id.
        :param bool override: If a document with document_id already exists
                              it will override that document.
        """
        self.__connect__()
        cloudant_doc = cloudant.document.Document(self._db, document_id)

        if cloudant_doc.exists() and not override:
            raise FlaskCloudantException(405, cloudant_doc['_id'])
        elif cloudant_doc.exists() and override:
            cloudant_doc.fetch()
            cloudant_doc.delete()

        doc = FlaskCloudantDocument(cloudant_doc, exists=False)

        try:
            doc.content(content)
        except AssertionError:
            raise FlaskCloudantException(700, 'Content', dict)
        doc.save()
        self.__disconnect__()
        return doc

    def delete(self, document_id):
        """
        Delete a document from the database using the `document_id`.

        :param str document_id: Document ID used on the database.
        """
        doc = self.get(document_id)
        self.__connect__()
        doc.delete()
        self.__disconnect__()

    @staticmethod
    def __connect__():
        FlaskCloudant.CLIENT.connect()

    @staticmethod
    def __disconnect__():
        FlaskCloudant.CLIENT.disconnect()


class FlaskCloudantDocument(object):
    """
    Creates a FlaskCloudantDocument.
    """

    def __init__(self, cloudant_doc, exists=True):
        if exists:
            if cloudant_doc.exists():
                self.document = cloudant_doc
                self.document.fetch()
            else:
                raise FlaskCloudantException(404, cloudant_doc['_id'])
        else:
            self.document = cloudant_doc

    def __repr__(self):
        return self.document['_id']

    def __str__(self):
        return self.document['_id']

    def content(self, content=None):
        """
        Used to set or get the content of a document.

        :param dict content: Dictionary containing the content to be
            inserted on the document. If the content is `None`, it will
            simply return the content from the current document.
        """
        if content is None:
            self.refresh();
            return dict(self.document)
        else:
            assert type(content) is dict
            for key, value in content.items():
                self.document.field_set(self.document, key, value)

    def exists(self):
        FlaskCloudant.__connect__()
        exists = self.document.exists()
        FlaskCloudant.__disconnect__()
        return exists

    def save(self):
        """
        Creates the document on the database.
        """
        self.document.create()

    def delete(self):
        """
        Deletes the document from the database.
        """
        self.document.delete()

    def refresh(self):
        FlaskCloudant.__connect__()
        self.document.fetch()
        FlaskCloudant.__disconnect__()


class FlaskCloudantView(object):
    """
    Creates a FlaskCloudantView.
    """
    pass
