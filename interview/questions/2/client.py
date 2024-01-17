# Copyright (c) 2021. Syntax Cloud Systems, LLC - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Client module to interact with the question's server."""

import random
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, List

import requests
import rich
from threading import Lock
from concurrent.futures import ThreadPoolExecutor


class EndpointNotFound(RuntimeError):
    """Raised when referencing an endpoint that does not exists on the server."""


class EndpointAlreadyLocked(RuntimeError):
    """Raised when trying to lock an endpoint which is already locked."""


class EndpointAlreadyUnlocked(RuntimeError):
    """Raised when trying to unlock an endpoint which is already unlocked."""


class ResourceNotFound(RuntimeError):
    """
    Raised whenever we try to access a resource that does not exists on an endpoint.

    This exception could also be raised if the endpoint didn't exist in the first place.
    """


class TryingToAccessResourceOnUnlockedEndpoint(RuntimeError):
    """Raised whenever we try to access a resource on an unlocked endpoint."""


@dataclass
class Endpoint:
    """
    Information about a specific endpoint.

    For the purpose of this question, it only contains a list of resource IDs
    this endpoint is able to provide.
    """

    resource_ids: List[int]


class Client:  # pylint: disable=too-few-public-methods
    """
    Client to interact with the question's server.

    Protected helper method have been implemented to perform all necessary REST
    API requests on the server.
    """

    def __init__(self, url: str, port: int):
        self.url = url
        self.port = port
        self.lock = Lock()  # Ensure there is a lock for synchronization
        self.session = requests.Session()  # Use a Session object for connection pooling

    def _find_endpoints_for_resources(self, registry: Dict[str, Endpoint], resource_ids: List[int]) -> List[str]:
        endpoints = []
        for resource_id in resource_ids:
            for endpoint, endpoint_info in registry.items():
                if resource_id in endpoint_info.resource_ids and endpoint not in endpoints:
                    endpoints.append(endpoint)
                    break
        return endpoints
    
    # def query_synchronized_resources(self, *resource_ids) -> Dict[int, str]:
    #     with self.lock:
    #         # Step 1: Query the registry from the server
    #         registry = self._get_registry()

    #         # Step 2: Find suitable endpoints that serve the necessary resources
    #         endpoints = self._find_endpoints_for_resources(registry, resource_ids)

    #         # Step 3: Lock all endpoints that will be used to query state
    #         locked_endpoints = []
    #         for endpoint in endpoints:
    #             try:
    #                 self._lock_endpoint(endpoint)
    #                 locked_endpoints.append(endpoint)
    #             except EndpointAlreadyLocked:
    #                 pass  # If already locked, we assume it's locked by this client

    #         # Step 4: Query the state of all desired resources
    #         resource_states = {}
    #         try:
    #             for resource_id in resource_ids:
    #                 for endpoint in endpoints:
    #                     if resource_id in registry[endpoint].resource_ids:
    #                         resource_states[resource_id] = self._get_resource(endpoint, resource_id)
    #                         break
    #         finally:
    #             # Step 5: Unlock all endpoints previously locked
    #             for endpoint in locked_endpoints:
    #                 try:
    #                     self._unlock_endpoint(endpoint)
    #                 except EndpointAlreadyUnlocked:
    #                     pass  # If already unlocked, we continue with the next one

    #         return resource_states
    


    def _get_registry(self) -> Dict[str, Endpoint]:
        """
        Query the endpoint registry from the server.

        Returns a dictionary which map the endpoint to the information contain
        wherein.
        """
        response = requests.get(f"http://{self.url}:{self.port}/registry")
        assert response.status_code == 200

        return {key: Endpoint(resource_ids=value["resources"]) for key, value in response.json().items()}

    def _lock_endpoint(self, endpoint: str):
        """
        Lock an endpoint.

        Locking an endpoint allows us to retrieve its state.
        """
        # response = requests.post(f"http://{self.url}:{self.port}/{endpoint}/lock")
        response = self.session.post(f"http://{self.url}:{self.port}/{endpoint}/lock")

        if response.status_code == 403:
            raise EndpointAlreadyLocked()

        if response.status_code == 404:
            raise EndpointNotFound()

        assert response.status_code == 200

    def _unlock_endpoint(self, endpoint: str):
        """
        Unlock an endpoint.

        It is important to always unlock endpoints after usage as the server as
        no way to unlock forgotten locked.
        """
        # response = requests.delete(f"http://{self.url}:{self.port}/{endpoint}/lock")
        response = self.session.delete(f"http://{self.url}:{self.port}/{endpoint}/lock")

        if response.status_code == 403:
            raise EndpointAlreadyUnlocked()

        if response.status_code == 404:
            raise EndpointNotFound()

        assert response.status_code == 200

    def _get_resource(self, endpoint: str, resource_id: int) -> str:
        """
        Query a specific resource's state from a specific endpoint.

        The state will be "synchronized" with the state of all locked endpoints.
        """
        response = self.session.get(f"http://{self.url}:{self.port}/{endpoint}/resource/{resource_id}")

        if response.status_code == 403:
            raise TryingToAccessResourceOnUnlockedEndpoint()

        if response.status_code == 404:
            raise ResourceNotFound()

        assert response.status_code == 200

        return response.json()["state"]

    def query_synchronized_resources(self, *resource_ids) -> Dict[int, str]:
        with self.lock:
            # Step 1: Query the registry from the server
            registry = self._get_registry()

            # Step 2: Find suitable endpoints that serve the necessary resources
            endpoints = self._find_endpoints_for_resources(registry, list(resource_ids))

            # Step 3: Lock all endpoints that will be used to query state
            locked_endpoints = self._lock_endpoints(endpoints)

            # Step 4: Query the state of all desired resources in parallel
            with ThreadPoolExecutor() as executor:
                future_to_resource_id = {
                    executor.submit(self._get_resource, endpoint, resource_id): resource_id
                    for resource_id in resource_ids
                    for endpoint in endpoints
                    if resource_id in registry[endpoint].resource_ids
                }
                resource_states = {future_to_resource_id[future]: future.result() for future in future_to_resource_id}

            # Step 5: Unlock all endpoints previously locked
            self._unlock_endpoints(locked_endpoints)

            return resource_states

    def _lock_endpoints(self, endpoints: List[str]) -> List[str]:
        locked_endpoints = []
        for endpoint in endpoints:
            try:
                self._lock_endpoint(endpoint)
                locked_endpoints.append(endpoint)
            except EndpointAlreadyLocked:
                pass  # If already locked, we assume it's locked by this client
        return locked_endpoints

    def _unlock_endpoints(self, endpoints: List[str]):
        for endpoint in endpoints:
            try:
                self._unlock_endpoint(endpoint)
            except EndpointAlreadyUnlocked:
                pass  # If already unlocked, we continue with the next one
            
# pylint: disable=protected-access,invalid-name


if __name__ == "__main__":
    client = Client("127.0.0.1", 5000)
    registry = client._get_registry()

    available_resources: List[int] = []

    for obj in registry.values():
        for resource in obj.resource_ids:
            if resource not in available_resources:
                available_resources.append(resource)

    request_times: List[float] = []
    futures: List[Future] = []

    def _timed_query(resource_ids: List[int]) -> float:
        try:
            start = time.time()
            client.query_synchronized_resources(*resource_ids)
            return time.time() - start
        except Exception as e:
            print(f"An error occurred during query: {e}")
            return float('inf')  # Return infinity to indicate a failed query

    with ThreadPoolExecutor(max_workers=100) as executor:
        for _ in range(0, 1000):
            number_of_resources = random.randint(0, 10)
            random.shuffle(available_resources)

            sample = list(random.sample(available_resources, number_of_resources))
            futures.append(executor.submit(_timed_query, sample))

        for future in futures:
            request_times.append(future.result())

    rich.print(
        {
            "minimum": min(request_times),
            "maximum": max(request_times),
            "average": sum(request_times) / len(request_times),
        }
    )
