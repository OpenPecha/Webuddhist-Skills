---
name: api_documentation-expert
description: Expert in FastAPI documentation, OpenAPI standards, and automatic docs generation.
---

# FastAPI Documentation Skill

## Overview
This skill provides instructions for generating, customizing, and maintaining comprehensive API documentation for FastAPI applications. It focuses on using Pydantic models for automatic schema generation, configuring Swagger UI and ReDoc, and ensuring compliance with OpenAPI standards.

## Core Capabilities
- **Automatic Docs Generation**: Leveraging `/docs` (Swagger UI) and `/redoc` for interactive API documentation.
- **Schema Modeling**: Using Pydantic to define input (`BaseModel`) and output schemas, which automatically appear in the documentation.
- **Metadata Customization**: Adding titles, descriptions, versions, and contact information to the FastAPI app instance.
- **Response Documentation**: Defining `response_model` to explicitly detail response structures.
- **Security Documentation**: Documenting JWT/OAuth2 flows, including padding and authentication methods.
- **Documentation Tagging**: Using tags to group endpoints and ordering routes in the UI.

## Key Guidelines & Best Practices
- **Define Models Early**: Define Pydantic models for all Request Bodies and Response Models.
- **Use Annotations**: Leverage Python's `Annotated` type for dependencies and validation to keep the documentation accurate.
- **Set Status Codes**: Explicitly define status codes (`status_code=201`, etc.) for accurate documentation.
- **Add Descriptions**: Use docstrings and `description` parameters in path operations to provide context in the docs.
- **Configure Metadata**:
    ```python
    app = FastAPI(
        title="My API",
        description="Detailed description",
        version="1.0.0",
        contact={"name": "API Team", "email": "dev@example.com"}
    )
    ```

## Example Documentation Structure
```python
from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
async def create_item(item: Item):
    """
    Create an item with all the information:
    - **name**: each item must have a name
    - **price**: price of the item
    """
    return item
```

## Endpoint Tests (pytest)

- **One test file per endpoint file**: For every module that defines FastAPI routes (e.g. `routers/items.py`), create a corresponding test file (e.g. `tests/test_items.py` or `tests/routers/test_items.py`) so coverage stays aligned with the API surface.
- **Use pytest**: Write tests with pytest. Use FastAPI's `TestClient` from `starlette.testclient` against the app instance to call endpoints without running a server.
- **Structure**:
  - Use a shared `client` fixture (or similar) that yields `TestClient(app)` so the same app and client are reused across tests.
  - Group tests by endpoint (e.g. one `class` or `describe` block per route, or clear naming like `test_create_item_returns_201`).
  - Test success paths (expected status codes and response bodies) and key error paths (validation, 404, 401, etc.) as appropriate.
- **Assertions**: Assert status codes (e.g. `assert response.status_code == 201`), response JSON shape, and critical fields. Use `response.json()` for JSON bodies.
- **Naming**: Mirror the endpoint module name in the test file name (e.g. `items.py` → `test_items.py`) and use descriptive test names that state the scenario and expected outcome.

### Example test file (pytest + TestClient)

```python
# tests/test_items.py
import pytest
from fastapi.testclient import TestClient

from main import app  # or wherever the FastAPI app is created

@pytest.fixture
def client():
    return TestClient(app)

def test_create_item_returns_201_and_body(client: TestClient):
    response = client.post("/items/", json={"name": "Widget", "price": 9.99})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Widget"
    assert data["price"] == 9.99

def test_create_item_validates_required_fields(client: TestClient):
    response = client.post("/items/", json={})
    assert response.status_code == 422
```
