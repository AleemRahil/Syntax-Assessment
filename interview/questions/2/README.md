# Context

You are tasked with completing a client module (see `client.py`) to communicate
with a legacy server which expose resource data following some bizarre
synchronization contract.

This module you will be written will replace the existing solution and, once
deployed, will be the *only way* to access the server moving forward.

A mock of this server has been implemented in `app.py` as a Flask application
which you can start with:

```
flask run
```

The server expose the following REST API:

* Sending a `GET /registry` request will yield a mapping of valid endpoint to
  use on this server and an object describing the resources available at that
  endpoint.

* You may get the state of a specific resource, from a specific endpoint, by
  sending a `GET /<endpoint>/resource/<resource_id>` where `<endpoint>` and
  `<resource_id>` are retrieved from the registry above.

* Simply querying the state of a resource is not valid: the endpoint must be
  "locked" first to synchronize state. This is accomplished using a `POST
  /<endpoint>/lock` to lock the specific endpoint.

* Once we are done working with an endpoint, it is important to call `DELETE
  /<endpoint>/lock`

Helper methods have already been implemented in `client.py` to execute all 4 of
those requests.

# Requirements

* You must implement the method `Client.query_synchronized_resources` in the
  `client.py` module.

* Given some resource IDs, the method must return the "synchronized" state of
  those resources by following these steps:

  - Query the registry from the server.
  - Find suitable endpoints that serve the necessary resources.
  - Lock all endpoints that will be used to query state (the "synchronization"
    bit comes from this requirement).
  - Query the state of all desired resources.
  - Unlock all endpoints previously locked.

* Your implementation should not deadlock, avoid starvation and be reasonably
  efficient (remember that the `client.py` module will be the only one used to
  communicate with the server moving forward).

# Testing

Running the `client.py` as a script will run a simulation against the mock
server (which must also be running!) which will test your implementation of
`Client.query_synchronized_resources` and give you some performance metrics.

If the simulation loops forever, you might have a deadlock in your
implementation (or there may be a bug in the simulator which is worth bonus
points if found by a candidate!)

# Simplifying Assumption

You may notice the mock implementation of the `GET`
`/<endpoint>/resource/<resource_id>` actually contains a race condition.

For the scope of this question, you may assume the race condition does not
exists.
