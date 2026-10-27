# Shared operational runtime

`gymarena_runtime` creates the common FastAPI metadata, liveness and database readiness endpoints used by the eight independently deployed services. It holds no domain entities, business rules, shared ORM models or cross-service database queries. Each service supplies its own expected table/view inventory and planned contract metadata, and receives only its own database connection settings.

The per-service Dockerfile copies this source into its own image. Changes require rebuilding the consuming images. Future business endpoints belong in their owning service, not this common runtime.
