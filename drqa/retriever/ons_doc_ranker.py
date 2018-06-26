"""Ranks documents using the ONS search service"""
import logging
from typing import List

logger = logging.getLogger(__name__)


class OnsDocRanker(object):
    host = 'http://localhost:5000'
    target = '/search/conceptual/ons'

    def get_urls_for_query(self, query: str) -> List[str]:
        import nltk
        from urllib import parse
        from drqa.retriever.utils import filter_word

        # Remove stop words
        tokens = [w for w in query.split() if filter_word(w) is False]

        # Build bigrams
        bigrams = [" ".join(b) for b in nltk.bigrams(tokens)]

        url_encoded_queries = [parse.quote(q) for q in bigrams]
        # Add original query
        original_filtered_query = " ".join(tokens)
        url_encoded_queries.append(parse.quote(original_filtered_query))

        # Remove dupes
        url_encoded_queries = list(set(url_encoded_queries))

        # Return list of target URLs to search
        return [self.host + self.target + "?q=%s" % q for q in url_encoded_queries]

    @staticmethod
    def search(query, k):
        import urllib
        import json
        from drqa.retriever.ons import content_type

        """
        Executes search queries against ONS search service
        :param query: 
        :param k: 
        :return: 
        """
        ids = []
        scores = []

        request = urllib.request.Request(query)
        request.add_header('Content-Type', 'application/json; charset=utf-8')

        content_types = [
            content_type.bulletin.name,
            content_type.article.name,
            content_type.static_qmi.name
        ]

        form = {
            "filter": content_types,
            "size": k
        }
        form_data = json.dumps(form)
        form_data_bytes = form_data.encode('utf-8')

        request.add_header('Content-Length', len(form_data_bytes))
        response = urllib.request.urlopen(request, form_data_bytes)
        response_data = response.read()

        json_data = json.loads(response_data)

        if 'result' in json_data:
            result = json_data['result']
            hits = result['results']

            logger.info("Got %d search results (k=%d)" % (len(hits), k))

            # Return IDs and scores
            for hit in hits:
                ids.append(hit['uri'])
                scores.append(hit['_score'])

        return ids, scores

    def closest_docs(self, query, k=1):
        """
        Gathers the closest documents by executing search queries and
        retrieving up to k documents per query
        :param query:
        :param k:
        :return:
        """
        targets: List[str] = self.get_urls_for_query(query)

        logger.info("Targets: %s" % targets)

        ids = []
        scores = []

        for target in targets:
            target_ids, target_scores = self.search(target, k)
            ids.extend(target_ids)
            scores.extend(target_scores)

        return ids, scores

    def batch_closest_docs(self, queries, k=1, num_workers=None):
        raise NotImplementedError("Batch closest docs not yet implemented")
