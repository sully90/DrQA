"""Documents, through ONS search."""
from drqa.retriever.doc_db import DocDB


class OnsSearchDB(DocDB):
    """ONS search backed document storage.

    Implements get_doc_text(doc_id).
    """
    host = 'http://localhost:5000'
    target = '/search'

    def __init__(self, **kwargs):
        pass

    def get_url_for_page(self, doc_id) -> str:
        from urllib import parse
        url_encoded_id = parse.quote(doc_id)
        return self.host + self.target + url_encoded_id

    def get_page(self, doc_id) -> dict:
        import json
        from urllib import request

        target: str = self.get_url_for_page(doc_id)

        request = request.urlopen(target)
        response = request.read()

        json_data = json.loads(response)

        if 'results' in json_data:
            results = json_data['results']
            hit: dict = results[0]

            return hit
        return None

    def get_doc_text(self, doc_id) -> str:
        """

        :param doc_id: uri of the document
        :return:
        """
        page = self.get_page(doc_id)

        if page is not None and 'description' in page:
            description = page['description']

            texts = []

            fields = ['title', 'headline1', 'headline2', 'headline3', 'summary']
            for field in fields:
                if field in description:
                    texts.append(description[field])

            return ". ".join(texts)
        return ""

    def close(self):
        pass

