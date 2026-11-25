#!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/queryquest-bootstrap.log) 2>&1

dnf install -y aws-cfn-bootstrap docker git
trap 'status=$?; /opt/aws/bin/cfn-signal -e "$status" --stack "${AWS::StackName}" --resource Server --region "${AWS::Region}"' EXIT
systemctl enable --now docker
install -d -m 700 /etc/queryquest
install -d -m 755 /opt/queryquest
install -d -m 700 -o 10001 -g 10001 /var/lib/queryquest

git clone --depth 1 https://github.com/dhaval-mistry/QueryQuest.git /opt/queryquest/source
cd /opt/queryquest/source
git fetch --depth 1 origin "${SourceCommit}"
git checkout --detach "${SourceCommit}"
docker build -t queryquest:production .

cat > /etc/queryquest/app.env <<'ENV'
AWS_REGION=${AWS::Region}
AWS_SEARCH_REGION=${AWS::Region}
BEDROCK_MODEL=us.anthropic.claude-sonnet-4-6
BEDROCK_MAX_TOKENS=4096
HOW_MANY_SEARCHES=5
MAX_SEARCHES_PER_RUN=2
AWS_SEARCH_MAX_RESULTS=5
QUERYQUEST_PUBLIC=true
QUERYQUEST_DATA_DIR=/data
QUERYQUEST_USAGE_SECRET=${UsageSecret}
QUERYQUEST_MONTHLY_LIMIT=1000
QUERYQUEST_DAILY_LIMIT=50
QUERYQUEST_VISITOR_DAILY_LIMIT=3
ENV
chmod 600 /etc/queryquest/app.env

cat > /etc/queryquest/nginx.conf <<'NGINX'
events { worker_connections 1024; }
http {
  server_tokens off;
  access_log off;
  client_max_body_size 1m;
  server {
    listen 80;
    location = /healthz { return 200 'ok'; add_header Content-Type text/plain; }
    location / {
      if ($http_x_queryquest_origin != '${OriginSecret}') { return 403; }
      proxy_pass http://127.0.0.1:7860;
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For $http_x_forwarded_for;
      proxy_set_header Connection '';
      proxy_buffering off;
      proxy_request_buffering off;
      proxy_read_timeout 900s;
      proxy_send_timeout 900s;
    }
  }
}
NGINX
chmod 600 /etc/queryquest/nginx.conf

docker pull nginx:1.28-alpine
cat > /etc/systemd/system/queryquest.service <<'SERVICE'
[Unit]
Description=QueryQuest research application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target
[Service]
Restart=always
RestartSec=5
TimeoutStartSec=0
ExecStartPre=-/usr/bin/docker rm -f queryquest
ExecStart=/usr/bin/docker run --name queryquest --network host --env-file /etc/queryquest/app.env -e GRADIO_SERVER_NAME=127.0.0.1 --mount type=bind,source=/var/lib/queryquest,target=/data --log-opt max-size=10m --log-opt max-file=3 queryquest:production
ExecStop=/usr/bin/docker stop -t 20 queryquest
[Install]
WantedBy=multi-user.target
SERVICE
cat > /etc/systemd/system/queryquest-proxy.service <<'SERVICE'
[Unit]
Description=QueryQuest CloudFront origin proxy
Requires=docker.service
After=docker.service queryquest.service
[Service]
Restart=always
RestartSec=5
TimeoutStartSec=0
ExecStartPre=-/usr/bin/docker rm -f queryquest-proxy
ExecStart=/usr/bin/docker run --name queryquest-proxy --network host --mount type=bind,source=/etc/queryquest/nginx.conf,target=/etc/nginx/nginx.conf,readonly --log-opt max-size=5m --log-opt max-file=2 nginx:1.28-alpine
ExecStop=/usr/bin/docker stop -t 10 queryquest-proxy
[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
systemctl enable --now queryquest queryquest-proxy
for attempt in $(seq 1 120); do
  if curl --fail --silent http://127.0.0.1:7860/ > /dev/null && curl --fail --silent http://127.0.0.1/healthz > /dev/null; then
    echo 'QueryQuest application and proxy are ready.'
    exit 0
  fi
  sleep 2
done
docker logs --tail 50 queryquest
exit 1
