# Run QueryQuest with Docker

The same Dockerfile packages either provider. It starts with AWS by default. No AWS resources are created, and no model requests or emails are sent just by starting the app.

## Build a package

Install and start Docker Desktop, then open a terminal in the repository root:

```powershell
cd C:\code\QueryQuest
docker build -t queryquest:aws .
```

For the preserved GPT version:

```powershell
docker build --build-arg APP_VARIANT=QueryQuest_GPT -t queryquest:gpt .
```

## Open the application

```powershell
docker run --rm --name queryquest -p 127.0.0.1:7860:7860 queryquest:aws
```

Open **http://127.0.0.1:7860**. This starts the interface; research additionally needs runtime credentials. Stop it with Ctrl+C. Run one provider at a time on this port.

## Supply credentials at runtime

For GPT, pass your existing private settings file:

```powershell
docker run --rm -p 127.0.0.1:7860:7860 --env-file QueryQuest_GPT/.env queryquest:gpt
```

For AWS, choose the method appropriate to the host:

- **AWS hosting:** attach an application IAM role to the server/container service. Boto3 uses that role. Do not set a laptop's `AWS_PROFILE` on the hosted app.
- **Another host, including Render:** configure supported noninteractive AWS credentials securely in that host's environment settings. A developer's `aws login` session is not a permanent production credential.
- **Local browser-login profile:** the container needs access to your local AWS profile and login cache. Sign in on the host first, then mount that directory for local development only:

```powershell
aws login --profile queryquest --region us-east-2
$queryquestAwsDirectory = Join-Path $env:USERPROFILE '.aws'
docker run --rm -p 127.0.0.1:7860:7860 --mount "type=bind,source=$queryquestAwsDirectory,target=/home/app/.aws" -e AWS_PROFILE=queryquest -e AWS_REGION=us-east-2 queryquest:aws
```

The mounted cache must be accessible to the container user, including writes needed for temporary credential refresh. This mount gives the local container access to that directory; use it only with your trusted local image. Never include it in an image or upload it to hosting. Other settings can be passed individually with `-e`, such as `-e MAX_SEARCHES_PER_RUN=2`.

Your `.env`, AWS profiles, Git history, local virtual environments, and caches are excluded from the Docker build context. The image runs as a non-root user and installs dependencies from the selected project's lockfile.

## AWS and Render portability

Both providers use the same start command: `python app.py`. Inside Docker, the app listens on `0.0.0.0:7860`. A hosting platform can supply `PORT`; the application and its health check use that value. Set credentials through the host, not Docker build arguments.

For a future Render deployment, select **Docker**, use the repository-root Dockerfile, and configure the runtime environment. The default image packages `QueryQuest_AWS`. Configure a Docker build argument to select `QueryQuest_GPT` instead.

The current package is a deployment building block. Before exposing billable research publicly, add persistent usage limits and complete the host's HTTPS, restart, and credential configuration.

## Verification

GitHub Actions tests both projects, builds both images, runs their tests inside the images, and checks that each interface starts without credentials. It also checks that the runtime user is non-root and `/app/.env` is absent. The workflow does not publish images or deploy a website.
