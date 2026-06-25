# ADR 0001: Use a Modular Monolith with Background Workers

## Status

Accepted

## Context

AI Analytics Hub combines five different capabilities:

- Apriori association mining
- Deep learning classification
- Question answering
- Text generation
- Named entity recognition

The platform must be professional enough for portfolio use, investor demos, and an eventual MVP, but it is also likely to be built by one developer or a small team.

The main architecture choices considered were:

- single Flask app with synchronous processing
- modular Flask monolith with background workers
- full microservices
- serverless-first architecture

## Decision

The platform will use a modular Flask monolith for web and API functionality, with background workers for long-running or resource-heavy tasks.

Key characteristics:

- Flask remains the main framework
- Blueprints separate domains and routes
- Services contain business and model logic
- Celery workers process training, Apriori jobs, and slow inference
- PostgreSQL stores relational state
- Redis supports queueing, caching, and rate limiting

## Rationale

- It preserves the existing Flask direction
- It is achievable for a small team
- It avoids unnecessary DevOps overhead at the current maturity level
- It still supports scaling web traffic and worker capacity independently
- It is much easier to test, document, and present professionally

## Consequences

Positive:

- Faster delivery
- Lower operational cost
- Clear path to production MVP
- Easier onboarding for future contributors

Negative:

- Strong team discipline is required to keep service boundaries clean
- Some modules may need to be extracted later if workload grows substantially

## Alternatives Rejected

### Single Flask App Without Workers

Rejected because training and analytics jobs would block request handling and hurt reliability.

### Full Microservices

Rejected for the first release because the infrastructure, CI/CD, testing, and observability overhead would be too high relative to product maturity.

### Serverless-Only

Rejected as the primary runtime because cold starts and long-running model tasks are a poor fit for the full workload, though serverless may still be useful for auxiliary batch functions later.
