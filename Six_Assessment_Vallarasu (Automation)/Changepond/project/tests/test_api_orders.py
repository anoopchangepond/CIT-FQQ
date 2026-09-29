"""Part C -- API testing thinking for GET /api/orders/{order_id}.

API Task 1: Test Case Design
----------------------------
Five test cases designed for this endpoint. Only one of them (the exact
scenario named in API Task 2, below) is implemented as automated code --
the rest are documented here as the exercise asks for.

1. Happy path
   Test name: test_get_order_success_returns_200_and_correct_fields
   Input: GET /api/orders/ORD-1001 (an order that exists)
   Expected result: HTTP 200; body contains all documented fields, with
       status reflecting the order's real state (e.g. "PAID"); no error
       payload.
   Why useful: this is the everyday path real traffic hits most often --
       if it breaks, every consumer of the endpoint breaks with it.

2. Not-found
   Test name: test_get_order_unknown_id_returns_404
   Input: GET /api/orders/ORD-9999 (syntactically valid, non-existent id)
   Expected result: HTTP 404 with a structured error body (e.g.
       {"error": "order_not_found"}) -- not a 200 with an empty body,
       and not a 500.
   Why useful: missing resources are one of the most common real-world
       cases (typos, stale links, deleted records); a clear 404 lets a
       client tell "doesn't exist" apart from "something broke".

3. Malformed / malicious input
   Test name: test_get_order_malformed_or_malicious_id_returns_400_safely
   Input: GET /api/orders/<bad id>, e.g. an empty id, a path-traversal
       attempt ("../../etc/passwd"), or an injection-style payload
       ("ORD-1001; DROP TABLE orders;--")
   Expected result: HTTP 400 (input rejected before reaching business
       logic), a generic error body, and no stack trace, SQL error text,
       or file-system detail leaked in the response.
   Why useful: this is as much a security test as a functional one -- it
       checks that input validation actually rejects hostile input
       instead of the API 500ing (which can leak internals) or, worse,
       executing it.

4. Response schema / type contract
   Test name: test_get_order_response_matches_schema_and_types
   Input: GET /api/orders/ORD-1001 (a valid, existing order)
   Expected result: the response contains exactly the documented fields
       (order_id, customer_id, amount, currency, status, created_at) --
       no more, no fewer -- with the right types: amount is a positive
       number, currency is a 3-letter string, status is one of the
       documented enum values, created_at parses as an ISO-8601 UTC
       timestamp.
   Why useful: a test that only checks one field's value (like Task 2's
       status == "PAID") can pass while the contract silently breaks
       elsewhere -- a renamed field, a type change, a malformed currency
       code. This catches consumer-breaking changes value-only checks miss.

5. Performance / SLA
   Test name: test_get_order_responds_within_sla
   Input: GET /api/orders/ORD-1001 (a normal, valid request)
   Expected result: the response completes within the agreed SLA (e.g.
       p95 < 300ms server-side, or < 1s end-to-end) for a single order
       lookup.
   Why useful: a functionally correct response that arrives too slowly
       still breaks the user experience and any caller's own timeout --
       this catches latency regressions (e.g. an accidental N+1 query)
       that pure correctness tests never would.

API Task 2: Simple Automated Test
----------------------------------
Implements the exact scenario from the brief: GET /api/orders/ORD-1001
returns HTTP 200 and status == "PAID". No real API is called --
`requests.get` is monkeypatched with a fake response, per the exercise's
own instructions -- so the test is deterministic and runs offline/in CI.
"""

import requests

ORDER_URL = "https://api.example.com/api/orders/ORD-1001"

ORD_1001_RESPONSE = {
    "order_id": "ORD-1001",
    "customer_id": "C001",
    "amount": 100.50,
    "currency": "GBP",
    "status": "PAID",
    "created_at": "2026-05-20T10:30:00Z",
}


class FakeResponse:
    """A tiny requests.Response stand-in, just enough for this test."""

    def __init__(self, status_code, json_body):
        self.status_code = status_code
        self._json_body = json_body

    def json(self):
        return self._json_body


def test_get_order_returns_200_and_status_paid(monkeypatch):
    def fake_get(url, timeout=None):
        assert url == ORDER_URL
        return FakeResponse(200, ORD_1001_RESPONSE)

    monkeypatch.setattr(requests, "get", fake_get)

    response = requests.get(ORDER_URL, timeout=5)

    assert response.status_code == 200
    assert response.json()["status"] == "PAID"
