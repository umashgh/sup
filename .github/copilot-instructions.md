# GitHub Copilot Instructions for Founder FIRE (Sup)

## Project Overview
This workspace contains a full-stack application "Founder FIRE" (Sup) designed to help founders plan their financial independence.
- **Backend**: Django 5.2 + Django REST Framework (DRF).
- **Frontend**: Ionic 8 + React 19 + Vite + TypeScript.
- **MCP Server**: Python-based Model Context Protocol server for knowledge base indexing.

## Architecture & Patterns

### Backend (`sup_backend/`)
- **Framework**: Django with DRF.
- **Authentication**: Token-based (`rest_framework.authentication.TokenAuthentication`).
  - Supports **Guest Login** via `core.views.GuestLoginView` which creates a temporary user.
- **API Structure**:
  - `urls.py` in each app defines routes.
  - `views.py` uses `ModelViewSet` for standard CRUD.
  - **CORS**: Configured via `corsheaders` middleware to allow frontend access.
- **Key Apps**:
  - `core`: Auth and user management.
  - `finance`: Family profiles, assets, income, expenses.
  - `ventures`: Startup ventures, costs, salaries.

### Frontend (`sup_frontend/`)
- **Framework**: Ionic React with Vite.
- **State Management**: Local state (`useState`) and effects (`useEffect`).
- **API Layer** (`src/services/api.ts`):
  - Centralized `axios` instance.
  - **Interceptors**: Handles 401 Unauthorized by clearing token and triggering re-login.
  - **Auth**: Token stored in `localStorage`.
- **UI Components**:
  - Use Ionic components (`IonPage`, `IonContent`, `IonButton`, etc.).
  - Forms use `IonInput`, `IonSelect`, etc.
  - **Toast Notifications**: Use `IonToast` for error/success feedback (e.g., in `VentureForm.tsx`).

### MCP Server (`sup_mcp/`)
- **Protocol**: JSON-RPC over stdio.
- **Purpose**: Indexes and serves documents from `ref/` to guide the app build with domain knowledge.
- **Entry Point**: `server.py`.
- **Design**: See `docs/mcp_design.md`.

## Domain & Requirements
- **Source of Truth**: The `docs/` folder contains all requirements and domain logic.
  - `docs/domain.md`: Core business logic, financial models, and projection algorithms.
  - `docs/mcp_design.md`: Design for the Knowledge Base server.
  - `docs/reqs.md`: Detailed application requirements.
- **Usage**: Consult these files before implementing complex logic (e.g., financial projections, asset classes).

## Developer Workflow

### Backend
- **Run Server**: `cd sup_backend && python3 manage.py runserver 0.0.0.0:8000`
- **Migrations**: `python3 manage.py migrate`
- **Tests**: `python3 manage.py test`

### Frontend
- **Run Dev Server**: `cd sup_frontend && npm run dev` (Vite)
- **Build**: `npm run build`
- **Lint**: `npm run lint`

## Coding Conventions
- **Frontend**:
  - Always handle API errors with user feedback (e.g., `IonToast`).
  - Use functional components with hooks.
  - Prefer `Ion*` components over native HTML elements for mobile consistency.
- **Backend**:
  - Use `ModelViewSet` for resources.
  - Ensure `permission_classes` are set (e.g., `IsAuthenticated` for user data).
  - Filter querysets by `request.user` to ensure data isolation.

## Key Files
- **Settings**: `sup_backend/sup_backend/settings.py` (CORS, Apps, DRF Config)
- **API Client**: `sup_frontend/src/services/api.ts` (Axios setup, Auth logic)
- **Routes**: `sup_backend/sup_backend/urls.py` (Main URL config)
