# Deployment Guide

## AWS Deployment

### 1. Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Docker installed locally
- Domain name (optional, for custom domain)

### 2. Infrastructure Setup

#### Option A: AWS Elastic Container Service (ECS)

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name ai-recruitment-system

# 2. Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t ai-recruitment-system .
docker tag ai-recruitment-system:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-recruitment-system:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-recruitment-system:latest

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name recruitment-cluster

# 4. Create task definition (see task-definition.json)
aws ecs register-task-definition --cli-input-json file://deployment/task-definition.json

# 5. Create service
aws ecs create-service \
  --cluster recruitment-cluster \
  --service-name recruitment-api \
  --task-definition recruitment-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### Option B: AWS Lambda + API Gateway

```bash
# 1. Package application
pip install -r requirements.txt -t package/
cp -r src package/
cd package && zip -r ../deployment.zip . && cd ..

# 2. Create Lambda function
aws lambda create-function \
  --function-name recruitment-api \
  --runtime python3.11 \
  --role arn:aws:iam::account-id:role/lambda-role \
  --handler src.api.handler \
  --zip-file fileb://deployment.zip \
  --timeout 30 \
  --memory-size 1024

# 3. Create API Gateway
aws apigatewayv2 create-api \
  --name recruitment-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:region:account-id:function:recruitment-api
```

### 3. Database Setup (RDS PostgreSQL)

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier recruitment-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password <secure-password> \
  --allocated-storage 20

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier recruitment-db \
  --query 'DBInstances[0].Endpoint.Address'

# Update DATABASE_URL in environment variables
```

### 4. Environment Configuration

Store secrets in AWS Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
  --name recruitment-system-secrets \
  --secret-string '{
    "ANTHROPIC_API_KEY": "sk-ant-xxx",
    "DATABASE_URL": "postgresql://...",
    "SMTP_PASSWORD": "xxx"
  }'

# Grant ECS task role access to secrets
# Update task definition to reference secrets
```

### 5. Load Balancer Setup

```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name recruitment-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
  --name recruitment-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --health-check-path /

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### 6. Auto Scaling

```bash
# Create auto scaling target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/recruitment-cluster/recruitment-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/recruitment-cluster/recruitment-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### 7. Monitoring & Logging

```bash
# CloudWatch Logs
aws logs create-log-group --log-group-name /ecs/recruitment-api

# CloudWatch Alarms
aws cloudwatch put-metric-alarm \
  --alarm-name high-cpu \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --period 300 \
  --statistic Average \
  --threshold 80 \
  --alarm-actions arn:aws:sns:region:account-id:alerts
```

## Google Cloud Platform (GCP) Deployment

### 1. Cloud Run Deployment

```bash
# Build and submit to Container Registry
gcloud builds submit --tag gcr.io/project-id/recruitment-system

# Deploy to Cloud Run
gcloud run deploy recruitment-api \
  --image gcr.io/project-id/recruitment-system \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=xxx \
  --set-secrets DATABASE_URL=recruitment-db-url:latest
```

### 2. Cloud SQL Setup

```bash
# Create PostgreSQL instance
gcloud sql instances create recruitment-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create recruitment_db --instance=recruitment-db

# Connect Cloud Run to Cloud SQL
gcloud run services update recruitment-api \
  --add-cloudsql-instances project-id:us-central1:recruitment-db
```

## DigitalOcean Deployment

### 1. App Platform

```bash
# Create app via doctl or web UI
doctl apps create --spec deployment/digitalocean-app.yaml

# Or use DigitalOcean App Platform UI:
# 1. Connect GitHub repository
# 2. Select Dockerfile
# 3. Configure environment variables
# 4. Deploy
```

### 2. Managed Database

```bash
# Create PostgreSQL database
doctl databases create recruitment-db \
  --engine pg \
  --region nyc3 \
  --size db-s-1vcpu-1gb
```

## Kubernetes Deployment

### 1. Create Kubernetes manifests

```yaml
# deployment/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recruitment-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recruitment-api
  template:
    metadata:
      labels:
        app: recruitment-api
    spec:
      containers:
      - name: api
        image: your-registry/recruitment-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: recruitment-secrets
              key: anthropic-api-key
```

```bash
# Apply manifests
kubectl apply -f deployment/k8s/
```

## CI/CD Setup

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker image
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker build -t recruitment-system .
          docker tag recruitment-system:latest $ECR_REGISTRY/recruitment-system:latest
          docker push $ECR_REGISTRY/recruitment-system:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster recruitment-cluster --service recruitment-api --force-new-deployment
```

## Post-Deployment

### 1. Health Check

```bash
curl https://your-domain.com/
# Should return: {"service": "AI Recruitment System", "status": "operational"}
```

### 2. Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f deployment/loadtest.py --host https://your-domain.com
```

### 3. Monitoring Setup

- Configure CloudWatch/Stackdriver dashboards
- Set up alerts for:
  - High error rates
  - High latency
  - Database connection issues
  - API rate limit hits

### 4. Backup Strategy

```bash
# Automated PostgreSQL backups
aws rds modify-db-instance \
  --db-instance-identifier recruitment-db \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"
```

## Scaling Recommendations

### Traffic Tiers

- **< 100 applications/day**: 1 container, db.t3.micro
- **100-1000 applications/day**: 2-3 containers, db.t3.small
- **1000-10000 applications/day**: 5-10 containers, db.t3.medium
- **> 10000 applications/day**: 10+ containers, db.r5.large, Redis cache

### Cost Optimization

1. Use reserved instances for steady-state workload
2. Implement request caching with Redis
3. Use spot instances for batch processing
4. Monitor Claude API usage and implement rate limiting

## Security Checklist

- [ ] Environment variables in secrets manager
- [ ] Database encrypted at rest
- [ ] SSL/TLS enabled
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] Regular security updates
- [ ] Audit logs enabled
- [ ] Backup strategy in place

## Rollback Procedure

```bash
# AWS ECS rollback
aws ecs update-service \
  --cluster recruitment-cluster \
  --service recruitment-api \
  --task-definition recruitment-task:previous-revision

# Kubernetes rollback
kubectl rollout undo deployment/recruitment-api
```
