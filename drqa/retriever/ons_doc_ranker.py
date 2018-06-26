"""Ranks documents using the ONS search service"""
import logging

logger = logging.getLogger(__name__)


class OnsDocRanker(object):
    host = 'http://localhost:5000'
    target = '/search/conceptual/ons'

    def get_url_for_query(self, query) -> str:
        from urllib import parse
        url_encoded_query = parse.quote(query)
        return self.host + self.target + "?q=%s" % url_encoded_query

    def search(self, query, k):
        import json
        import urllib.request

        from drqa.retriever.ons import content_type

        target: str = self.get_url_for_query(query)

        request = urllib.request.Request(target)
        request.add_header('Content-Type', 'application/json; charset=utf-8')

        content_types = [
            content_type.bulletin.name,
            content_type.article.name
        ]

        form = {
            "filter": content_types,
            "size": k
        }
        form_data = json.dumps(form)
        form_data_bytes = form_data.encode('utf-8')

        request.add_header('Content-Length', len(form_data_bytes))

        return urllib.request.urlopen(request, form_data_bytes)

    def closest_docs(self, query, k=1):
        """
        Queries the ONS search service to get closest documents
        :param query:
        :param k:
        :return:
        """
        import json

        response = self.search(query, k)
        response_data = response.read()

        json_data = json.loads(response_data)

        if 'result' in json_data:
            result = json_data['result']
            hits = result['results']

            logger.info("Got %d search results (k=%d)" % (len(hits), k))

            # Return IDs and scores
            ids = []
            scores = []
            for hit in hits:
                ids.append(hit['uri'])
                scores.append(hit['_score'])

            return ids, scores

        return [], []

    def batch_closest_docs(self, queries, k=1, num_workers=None):
        raise NotImplementedError("Batch closest docs not yet implemented")
