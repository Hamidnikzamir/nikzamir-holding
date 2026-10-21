# nikzamir-holding (monorepo)

This repository contains all Cloudflare Workers that belong to the holding company.
Each worker lives in its own sub-project under pps/, allowing independent development, deployment, and versioning while sharing common tooling and dependencies.

## Architecture
- pps/holding-core: Shared libraries/utilities
- pps/directyar-worker: DirectYar worker
- pps/quantum-admin: Quantum Admin worker
- pps/sultan-trust: Sultan Trust worker

## Development
Run pnpm install at the root, then pnpm --filter <app-name> dev to start a specific worker.
