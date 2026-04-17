import requests

base_url = "http://13.250.189.160/v2"
production_url = "https://api-aq25662yyq-uc.a.run.app/v2"


def get_text(text_id):
    """
    Fetch text from the server at /texts/as endpoint.
    Returns the JSON response.
    """
    url = f"{base_url}/texts/{text_id}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_text_from_server(edition_id):
    url = f"{base_url}/editions/{edition_id}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_edition_id_from_text_id(text_id):
    url = f"{base_url}/texts/{text_id}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["id"]


def get_text_content(text_id=None, edition_id=None, span_start=None, span_end=None):
    """
    Fetch content for a given edition_id, optionally restricting to a span.
    """
    if edition_id is None:
        if text_id is None:
            raise ValueError("Either edition_id or text_id must be provided")
        edition_id = get_edition_id_from_text_id(text_id)
    url = f"{base_url}/editions/{edition_id}/content"
    params = {}
    if span_start is not None:
        params["span_start"] = span_start
    if span_end is not None:
        params["span_end"] = span_end
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def get_segment_related(edition_id, span_start, span_end, transform=False):
    """
    Call the /segment-related endpoint for a particular edition and span.
    """
    url = f"{production_url}/instances/{edition_id}/segment-related"
    params = {
        "span_start": span_start,
        "span_end": span_end,
        "transform": str(transform).lower(),
    }
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def get_segmentations(edition_id):
    """
    Fetch segmentations for a given edition_id from the server.
    """
    url = f"{base_url}/editions/{edition_id}/segmentations"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_related_segments(
    edition_id,
    segment_id=None,
    span_start=None,
    span_end=None,
    transform=False,
):
    """
    Fetch related segments for a particular edition and (optionally) segment_id,
    span_start, span_end. All of segment_id, span_start, and span_end are optional.
    """
    url = f"{production_url}/instances/{edition_id}/segment-related"
    params = {"transform": str(transform).lower()}
    if segment_id is not None:
        params["segment_id"] = segment_id
    if span_start is not None:
        params["span_start"] = span_start
    if span_end is not None:
        params["span_end"] = span_end
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()
