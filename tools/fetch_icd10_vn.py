import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


DEFAULT_API_BASE = "https://ccs.whiteneuron.com/api/ICD10"


def collect_catalog(
    fetch_json,
    api_base=DEFAULT_API_BASE,
    language="vi",
    fetch_many=None,
):
    api_base = api_base.rstrip("/")
    root_url = f"{api_base}/root?{urlencode({'lang': language})}"
    frontier = [(value, None, ()) for value in _response_data(fetch_json(root_url))]
    found = {}
    expanded = set()
    fetch_many = fetch_many or (lambda urls: [fetch_json(url) for url in urls])

    while frontier:
        requests = []
        for value, parent, ancestors in frontier:
            item = _parse_node(value, parent)
            identity = (item["model"], item["id"])
            if identity in ancestors:
                raise ValueError(f"hierarchy cycle at {identity!r}")

            previous = found.get(identity)
            if previous is not None and previous != item:
                raise ValueError(f"conflicting duplicate node: {identity!r}")
            found.setdefault(identity, item)

            if item["is_leaf"] or identity in expanded:
                continue
            expanded.add(identity)
            child_url = (
                f"{api_base}/childs/{quote(item['model'], safe='')}?"
                + urlencode({"id": item["id"], "lang": language})
            )
            requests.append((child_url, item, ancestors + (identity,)))

        responses = fetch_many([request[0] for request in requests])
        if len(responses) != len(requests):
            raise ValueError("batch fetch returned the wrong response count")
        frontier = []
        for (_, item, lineage), response in zip(requests, responses, strict=True):
            parent_ref = {"model": item["model"], "id": item["id"]}
            frontier.extend(
                (child, parent_ref, lineage)
                for child in _response_data(response)
            )

    return sorted(found.values(), key=_sort_key)


def canonical_snapshot(nodes, api_base=DEFAULT_API_BASE, language="vi"):
    payload = {
        "format_version": 1,
        "source_api": api_base.rstrip("/"),
        "language": language,
        "nodes": sorted(nodes, key=_sort_key),
    }
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def fetch_json(url, timeout=30):
    request = Request(
        url,
        headers={"User-Agent": "medical-race-ontology-acquisition/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_json_batch(urls, timeout=30, workers=8):
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda url: fetch_json(url, timeout), urls))


def _response_data(response):
    if (
        not isinstance(response, dict)
        or response.get("status") != "success"
        or not isinstance(response.get("data"), list)
    ):
        raise ValueError("invalid hierarchy response")
    return response["data"]


def _parse_node(value, parent):
    if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
        raise ValueError("invalid hierarchy node")
    data = value["data"]
    model = value.get("model")
    node_id = value.get("id")
    code = data.get("code")
    name = data.get("name")
    is_leaf = value.get("is_leaf")
    if (
        not isinstance(model, str)
        or not model
        or not isinstance(node_id, str)
        or not node_id
        or data.get("id") != node_id
        or not isinstance(code, str)
        or not code
        or not isinstance(name, str)
        or not name
        or type(is_leaf) is not bool
    ):
        raise ValueError("invalid hierarchy node")
    if parent is not None and (
        not isinstance(parent, dict)
        or set(parent) != {"model", "id"}
        or not all(isinstance(parent[field], str) and parent[field] for field in parent)
    ):
        raise ValueError("invalid parent reference")
    return {
        "model": model,
        "id": node_id,
        "code": code,
        "name": name,
        "is_leaf": is_leaf,
        "parent": parent,
    }


def _sort_key(item):
    return item["code"], item["model"], item["id"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--language", default="vi")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers must be between 1 and 16")

    nodes = collect_catalog(
        lambda url: fetch_json(url, args.timeout),
        args.api_base,
        args.language,
        lambda urls: fetch_json_batch(urls, args.timeout, args.workers),
    )
    data = canonical_snapshot(nodes, args.api_base, args.language)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(data)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "node_count": len(nodes),
                "sha256": hashlib.sha256(data).hexdigest(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
