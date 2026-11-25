# AWS deployment

This deployment uses the AWS project account in Ohio (`us-east-2`). It creates one `t3.small` Linux EC2 server, a 25 GB encrypted disk, a fixed public IPv4 address, a restricted security group, an application role, and a CloudFront HTTPS address.

## Live deployment

- Website: **https://d2rof5vhi9w78g.cloudfront.net**
- AWS project account: `456823161025`; region: `us-east-2` (Ohio).
- CloudFormation stack: `queryquest-public`.
- EC2 server: `i-0b76d447d79ec9479`; CloudFront distribution: `E31JANOIBKS01F`.
- Application revision: `d663765895cae590c7568f5bb4afb319f1eee78b`.

In the AWS console, select the project account and Ohio region, then open **CloudFormation → queryquest-public** to find the resources. For a server terminal, use **Systems Manager → Session Manager → Start session**, then select the EC2 server above. The website stays running when there are no visitors; it does not sleep automatically.

Verified on November 25, 2026 (UTC): public HTTPS returned 200, HTTP redirected to HTTPS, and a live research request completed planning, two AWS searches, and Claude article generation with source links. After deliberately stopping the app container, systemd restarted it, the public page recovered, and SQLite usage counters remained intact. Both services are enabled at boot; the application obtained AWS credentials from its server role.

Expected hosting baseline is about **$21/month**, before credits, model calls, search overages, data transfer, and logs. No load balancer, NAT gateway, domain purchase, or SSH key is required. CPU credits are in standard mode to avoid surplus-credit charges.

## Access and operation

- Visitors use the AWS-provided `https://...cloudfront.net` address. HTTP redirects to HTTPS.
- CloudFront caching is disabled for the interactive app, including its streaming progress.
- The origin uses HTTP; inbound network access is restricted to AWS CloudFront origin servers, and Nginx validates a per-deployment secret header. This is browser-facing HTTPS, not end-to-end TLS to the EC2 origin.
- Administration uses AWS Systems Manager, with no SSH port open.
- The server uses an IAM role limited to the selected Claude model, web search, bootstrap signals, and standard Systems Manager connectivity. No laptop credentials are copied.
- Systemd starts the app and proxy at boot and restarts either process if it exits.
- Public preview limits are 1,000 research attempts per UTC month, 50 per UTC day globally, and 3 per visitor address per UTC day. Failed attempts count because they can consume API usage. Limits are stored in SQLite on the server disk and survive process restarts and reboots.
- Visitor addresses are stored only as keyed hashes. Questions and articles are not stored in this database. People sharing an address share its allowance.
- Email delivery is disabled for the public preview. The local application keeps its optional email behavior.

## Files

`aws_stack.py` generates the CloudFormation template. `server-bootstrap.sh` installs Docker, builds the exact GitHub revision, configures the services, and signals readiness. `manage.py` validates account/region and manages the change set.

Use the `queryquest` browser-login profile locally. Generated secrets are CloudFormation NoEcho parameters; do not print or commit them. The local deployment state records resource identifiers only and belongs in the ignored `.tmp/` directory.

## Updates and stopping

Application updates should use Systems Manager to fetch a specific Git revision, rebuild the image, and restart `queryquest`. Cloud-init does not automatically rerun every time a CloudFormation parameter changes.

Stopping EC2 makes the site unavailable and stops instance-compute charges; the disk and allocated IPv4 address can still incur charges. Deleting the stack removes its resources and deletes the root disk, including usage counters. Take a backup before deletion if those counters matter. Do not delete or change your AWS management account.
