# Copyright (c) 2021. Syntax Cloud Systems, LLC - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Mock server implemented in Flask."""

import time
import uuid
from dataclasses import asdict, dataclass
from random import randint
from threading import Lock
from typing import Dict, List, Set

import requests
from flask import Flask, jsonify

NUMBER_OF_ENDPOINTS = 50

MINIMUM_RESOURCE_ID = 0
MAXIMUM_RESOURCE_ID = 50
MAXIMUM_RESOURCES_BY_ENDPOINT = 10

RANDOM_WORDS_SOURCE = "https://www.mit.edu/~ecprice/wordlist.10000"

API = Flask(__name__)


@dataclass
class Endpoint:
    """State of a resource on a specific endpoint."""

    resources: List[int]
    lock: Lock


def initialize_registry() -> Dict[str, Endpoint]:
    """Initialize a random registry of endpoint to resources exposed mapping."""
    mock_registry: Dict[str, Endpoint] = {}
    random_words = set(requests.get(RANDOM_WORDS_SOURCE).text.splitlines())

    for _ in range(0, NUMBER_OF_ENDPOINTS):
        endpoint = random_words.pop()
        resources: Set[int] = set()

        for _ in range(0, randint(0, MAXIMUM_RESOURCES_BY_ENDPOINT)):
            resource_id = randint(MINIMUM_RESOURCE_ID, MAXIMUM_RESOURCE_ID + 1)
            resources.add(resource_id)

        mock_registry[endpoint] = Endpoint(resources=list(resources), lock=Lock())

    return mock_registry


REGISTRY = initialize_registry()


@API.route("/registry", methods=["GET"])
def registry():
    """Return the full registry in JSON."""
    return jsonify(
        {name: {"resources": endpoint.resources, "locked": endpoint.lock.locked()} for name, endpoint in REGISTRY.items()}
    )


@API.route("/<endpoint>/lock", methods=["POST"])
def lock(endpoint: str):
    """Lock the given endpoint for exclusive access."""
    if endpoint not in REGISTRY:
        return jsonify({"error": f"'{endpoint}' not found"}), 404

    if not REGISTRY[endpoint].lock.acquire(blocking=False):
        return jsonify({"error": f"'{endpoint}' is already locked"}), 403

    return jsonify({}), 200


@API.route("/<endpoint>/lock", methods=["DELETE"])
def unlock(endpoint: str):
    """Unlock a previously locked endpoint."""
    if endpoint not in REGISTRY:
        return jsonify({"error": f"'{endpoint}' not found"}), 404

    try:
        REGISTRY[endpoint].lock.release()
    except RuntimeError:
        return jsonify({"error": f"'{endpoint}' is already unlocked"}), 403

    return jsonify({}), 200


@API.route("/<endpoint>/resource/<resource_id>", methods=["GET"])
def get(endpoint: str, resource_id: str):
    """Get mocked state associated with a resource ID."""
    if endpoint not in REGISTRY:
        return jsonify({"error": f"'{endpoint}' not found"}), 404

    if int(resource_id) not in REGISTRY[endpoint].resources:
        return jsonify({"error": f"'{endpoint}' does not expose resource '{resource_id}'"}), 404

    if not REGISTRY[endpoint].lock.locked:  # If this was real life, this would be a race condition.
        return jsonify({"error": f"'{endpoint}' must be locked to access its state"}), 403

    time.sleep(0.1)  # To be able to compute meaningful performance metrics.

    return jsonify({"state": uuid.uuid4().hex}), 200
