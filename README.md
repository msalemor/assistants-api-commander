# Assistants API Playground

An Assistants API playground.

## Requirements

- Create an `.env` file at `src\backend`
- Add the following values:
```bash
OPENAI_URI=https://<NAME>.openai.azure.com/
BASE_URL=https://<NAME>.openai.azure.com/openai
OPENAI_KEY=<API_KEY>
OPENAI_GPT_DEPLOYMENT=<DEPLOYMENT_NAME>
```

## Frontend
- SolidJS
```json
"dependencies": {
    "@solid-primitives/storage": "^2.1.2",
    "axios": "^1.6.7",
    "solid-js": "^1.8.7",
    "solid-markdown": "^2.0.0",
    "solid-spinner": "^0.2.0"
  }
```

## Backend
- Python 3.10
- [Requirements](src/backend/requirements.txt)

## Deploying as a docker container

- Open to [Makefile](Makefile)
- Update the following variables:
```text
TAG=0.0.5
DOCKER_PATH=am8850
DOCKER_NAME=aiassistant01
```
- Type: `make deploy`
