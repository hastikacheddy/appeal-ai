# Deploying Appeal

Appeal is one container that listens on port 8000. The judges need a public URL they can open without logging in.

## Option A: Nebius Serverless Endpoint (recommended: shows more Nebius usage)

1. Push the image to a registry Nebius can pull from. Docker Hub or GHCR works, or use the Nebius Container Registry (see its docs):
   ```bash
   docker build --platform linux/amd64 -t <registry>/appeal:v1 .
   docker push <registry>/appeal:v1
   ```
2. Create a CPU endpoint. Appeal does no local inference; all model calls go to Token Factory, so a small CPU preset is enough:
   ```bash
   nebius ai endpoint create \
     --name appeal \
     --image <registry>/appeal:v1 \
     --platform cpu-d3 --preset 4vcpu-16gb \
     --container-port 8000 \
     --public
   ```
   - Pass `NEBIUS_API_KEY` and `TAVILY_API_KEY` as environment variables. Run `nebius ai endpoint create --help` for the exact env flag on your CLI version.
   - **Don't** enable token auth for the public web app, or judges' browsers can't open it.
3. Get the HTTPS URL:
   ```bash
   ID=$(nebius ai endpoint get-by-name --name appeal --format jsonpath='{.metadata.id}')
   nebius ai endpoint get "$ID" --format json | jq -r '.status.public_endpoints[] | select(startswith("https://"))'
   ```

Reference: https://docs.nebius.com/serverless/quickstart/endpoints

## Option B: any container host (Render, Railway, Fly.io)

Point the host at this repo's Dockerfile and set `NEBIUS_API_KEY` and `TAVILY_API_KEY`. The rules only require a runtime call to Token Factory, and every live run makes several.

## Before you submit

- [ ] Run `python -m app.check_models` and confirm all four model ids are found
- [ ] Open the public URL in a private window, click **Try a sample letter** and confirm the badge says **Live · Nebius Token Factory**
- [ ] Keep enough Token Factory and Tavily credit to cover judging (Dec 1–15)
