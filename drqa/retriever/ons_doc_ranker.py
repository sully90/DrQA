"""Ranks documents using the ONS search service"""
import logging
from typing import List

logger = logging.getLogger(__name__)


class OnsDocRanker(object):
    host = 'http://localhost:5000'
    target = '/search/conceptual/ons/content'

    def get_urls_for_query(self, query: str) -> List[str]:
        import nltk
        from urllib import parse
        from drqa.retriever.utils import filter_word

        # Remove stop words
        tokens = [w.lower() for w in query.split() if filter_word(w) is False]

        bigrams = [b for b in nltk.bigrams(tokens)]

        url_encoded_queries = [parse.quote(" ".join(b)) for b in bigrams]

        # Combine and url encode
        filtered_query = " ".join(tokens)

        # Add filtered and unfiltered queries
        url_encoded_queries.extend([parse.quote(filtered_query), parse.quote(query.lower())])

        # Remove dupes
        url_encoded_queries = list(set(url_encoded_queries))

        # Return list of target URLs to search
        return [self.host + self.target + "?q=%s" % q for q in url_encoded_queries]

    @staticmethod
    def search(query, k):
        import urllib
        import json
        import numpy as np
        from drqa.retriever.ons import content_type

        """
        Executes search queries against ONS search service
        :param query: 
        :param k: 
        :return: 
        """
        ids = []
        scores = []

        request = urllib.request.Request(query + "&size=%d" % k)
        request.add_header('Content-Type', 'application/json; charset=utf-8')

        content_types: List[str] = [
            content_type.bulletin.name,
            # content_type.article.name,
            # content_type.static_adhoc.name,
            # content_type.product_page.name
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

        if 'results' in json_data:
            hits = json_data['results']

            logger.info("Got %d search results (k=%d)" % (len(hits), k))

            # Return IDs and scores
            for hit in hits:
                ids.append(hit['uri'])
                scores.append(hit['_score'])

        # Sort and return
        ids = np.array(ids)
        scores = np.array(scores)

        inds = scores.argsort()

        sorted_ids: np.ndarray = ids[inds]
        sorted_scores: np.ndarray = scores[inds]

        return sorted_ids.tolist(), sorted_scores.tolist()

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

        collected_hits = {}

        for target in targets:
            target_ids, target_scores = self.search(target, k)

            for target_id, target_score in zip(target_ids, target_scores):
                if target_id not in collected_hits:
                    collected_hits[target_id] = target_score
                elif collected_hits[target_id] < target_score:
                    collected_hits[target_id] = target_score

        ids = []
        scores = []
        for target_id in collected_hits:
            ids.append(target_id)
            scores.append(collected_hits[target_id])

        return ids, scores

    def batch_closest_docs(self, queries, k=1, num_workers=None):
        raise NotImplementedError("Batch closest docs not yet implemented")
