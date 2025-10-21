# NYU DevOps Project Template

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![Build Status](https://github.com/CSCI-GA-2820-FA25-001/lab-github-actions/products/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA25-001/products/actions)

# Product Service

A RESTful API service for managing products built with Flask and PostgreSQL.

## Overview

This Product Service provides a complete Create, Read, Update, Delete and List API for managing product information. It's built with Flask and uses PostgreSQL for data persistence.

## Features

- ✅ Create new products
- ✅ Retrieve individual products
- ✅ Update existing products  
- ✅ Delete products
- ✅ Data validation and error handling
- ✅ Comprehensive test coverage
- ✅ Database migrations
- ✅ Logging configuration

## Setup

### 1. Reposity Configuration
```bash
git clone https://github.com/CSCI-GA-2820-FA25-001/products.git
```

### 2. Initialize Database
```bash
flask db-create
```

### 3. Run the Application
```bash
flask run
```

## API Endpoints

### Base URL
All endpoints are relative to http://localhost:8080/

### 1. Get Service Information
GET /
Returns service status and information.

### 2. Create a Product
POST /products
Creates a new product.

#### Request Body:
```bash
json
{
  "id": "SKU-000001",
  "name": "Product Name",
  "description": "Product description",
  "price": 29.99,
  "image_url": "https://example.com/image.jpg",
  "available": true
}
```
Required Fields: ```id```, ```name```, ```price```
Optional Fields: ```description```, ```image_url```, ```available``` (defaults to ```true```)

### 3. Get a Product
GET /products/{product_id}
Retrieves a specific product by ID.

#### Parameters:

```product_id``` (string) - The product identifier

#### Response:
```bash
json
{
  "id": "SKU-000001",
  "name": "Product Name",
  "description": "Product description",
  "price": 29.99,
  "image_url": "https://example.com/image.jpg",
  "available": true
}
```
#### Status Codes:

```200 OK``` - Product found

```404 Not Found``` - Product not found

### 4. Update a Product
PUT /products/{product_id}
Updates an existing product.

#### Parameters:

```product_id``` (string) - The product identifier

#### Request Body: 
Same as create, all fields required for update

#### Response:

```200 OK``` - Product updated successfully

```404 Not Found``` - Product not found

```400 Bad Request``` - Invalid data

### 5. List a Product
GET /products Retrieves a list of products in the database.
```bash
json
{
  {
  "id": "SKU-000001",
  "name": "Product Name",
  "description": "Product description",
  "price": 29.99,
  "image_url": "https://example.com/image.jpg",
  "available": true
  },
  {
    {
    "id": "SKU-000002",
    "name": "Product Name 2",
    "description": "Product description 2",
    "price": 39.99,
    "image_url": "https://example.com/image2.jpg",
    "available": false
  }
}
```
```200 OK``` - Successfully retrieved a list of products

### 6. Delete a Product
DELETE /products/{product_id}
Deletes a product.

#### Parameters:

```product_id``` (string) - The product identifier

#### Response:

```204 No Content``` - Product deleted successfully

```404 Not Found``` - Product not found (still returns 204)

## Testing
### Run All Tests
```bash
make test
```

## Contents

The project contains the following:

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
