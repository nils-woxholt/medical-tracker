# Project

## overview
This is a medical tracker service that allows users to log in and track their medical data over time. The service includes user authentication, data entry, and data visualization features.

## starter prompt 

I'm building a SAAS medical tracker web-app - a one stop diary about my conditions, doctors, symptoms and medication. 

**It must have:**
- landing page (summary last 5 medication logs, last 5 symptom logs, a 'how do you feel vs yesterday' better or worse), 
- medication page (log medication taken; maintenance of medication meta: purpose, frequency, prescribing doctor, current or not), 
- symptom page (symptom definition + logging), 
- doctor page (name, related condition, phone, email, description), 
- condition passport (diagnosed conditions), 
- notes (tag a doctor or medication and upload a file), login multi-patient system. 

**It must be:**
- easy to navigate, 
- mobile friendly, 
- visual with graphs and visuals to show progress.
- It must look sleek and trust-worthy. 
- It must use a colloquial but sympathetic language tone. 


## backend Service

This folder contains the backend service for our application. 

- this is a python FastAPI project
- always run using `uv run` 
- always test using `uv run pytest`
- DONT use `pip install` - ALWAYS use `uv add`
- when running ALEMBIC migrations use `uv run alembic`
- NOTE make sure that you are in the backend folder when running the command

### Backend technology

- python
- FastAPI
- SQLite
- Alembic (for migrations)
- passlib (for password hashing)
- pytest (for testing)
- UV (for running the app and managing dependencies)

## Frontend Service

- The Frontend is built with nextjs
- always run using 'npm run dev' command
- make sure that you are in the frontend folder by using the full path `cd C:\dev\lseg\spec-kit\todo\frontend` when running the command
- when running playwright tests, run them silently with `npx playwright test --quiet` to reduce noise in the output
- when running npm tests, run them silently with `npm test -- --silent` to reduce noise in the output

### Frontend technology

- nextjs
- React
- Typescript
- jest (for testing)
- Playwright (for e2e testing)
- styled using tailwindcss and shadcn/ui components

### spec-kit tasks

- when completing tasks, update the checklist in tasks.md to indicate that the task is complete
