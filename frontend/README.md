# MedVault Frontend

Next.js 16 application for the MedVault web client.

## Architecture

```
src/
├── app/            # Next.js App Router (route groups)
├── features/       # Feature-first modules
├── components/     # Shared UI components (shadcn/ui, layout, common)
├── lib/            # API client, utilities, validators
├── hooks/          # Shared React hooks
├── stores/         # Zustand stores (client state)
├── types/          # Shared TypeScript types
└── providers/      # React context providers
```

Each feature module contains:

```
components/ → hooks/ → api/ → schemas/ → types/
```

Server state is managed with TanStack Query. Client state uses Zustand.

## Prerequisites

- Node.js 20+
- pnpm (recommended) or npm

## Setup

```bash
cd frontend
pnpm install
cp .env.example .env.local
```

Start the development server:

```bash
pnpm dev
```

The app runs at [http://localhost:3000](http://localhost:3000).

## Feature Modules

| Feature          | Route              | Description                    |
| ---------------- | ------------------ | ------------------------------ |
| `auth`           | `/login`, `/register` | Authentication              |
| `dashboard`      | `/dashboard`       | Overview and quick actions     |
| `documents`      | `/documents`       | Document browsing              |
| `upload`         | `/upload`          | File upload                    |
| `timeline`       | `/timeline`        | Chronological medical history  |
| `chat`           | `/chat`            | AI assistant                   |
| `family-members` | `/family-members`  | Family member management       |
| `settings`       | `/settings`        | Account settings               |

## Documentation

See [docs/FSD.md](../docs/FSD.md) for the full frontend specification.
