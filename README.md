# Final Transcript Service

An automated transcription service that processes VideoAsk form responses and converts audio/video to text using Rev.ai API.

## Features

- Webhook integration with VideoAsk
- Audio/video file transcription using Rev.ai
- NLP quality checks and transcript enhancement
- Google Sheets integration for result storage
- Support for manual transcription requests
- Comprehensive test suite
- Docker containerization
- CI/CD with GitHub Actions

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/Cordycepsers/final-transcript.git
cd final-transcript
```

2. Run the setup script:
```bash
bash setup_dev.sh
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the development server:
```bash
flask run --port 8000
```

## Docker Development

Use Docker Compose for local development with containers:

```bash
docker-compose up --build
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## API Endpoints

### Webhook Endpoint
- `POST /webhook` - Receives VideoAsk form responses

### Manual Transcription
- `POST /manual/transcribe` - Submit manual transcription request
- `GET /manual/status/<job_id>` - Check transcription status
- `POST /manual/batch` - Submit batch transcription requests

### Quality Check
- `GET /transcript/quality/<job_id>` - Get transcript quality metrics

## GitHub Codespaces

This repository is configured for GitHub Codespaces. Click "Code > Open with Codespaces" to start development.

## Deployment

The service uses GitHub Actions for CI/CD:

1. Tests run on every push and pull request
2. Main branch deployments trigger:
   - Docker image build
   - Push to Amazon ECR
   - ECS service update

Required secrets:
- `REV_AI_API_KEY`
- `WEBHOOK_CALLBACK_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## License

MIT