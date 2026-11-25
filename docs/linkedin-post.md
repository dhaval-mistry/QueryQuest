# LinkedIn post

Attach `assets/queryquest-aws-architecture.png` as the image, then paste the text below.

---

From a question to a research report?with sources you can actually open. ??

I built QueryQuest, an AI research assistant powered by Claude on Amazon Bedrock and AWS AgentCore Web Search.

The workflow is straightforward:
Plan the research ? Collect web evidence ? Write the article ? Check structure and source references.

Behind the interface: Python, Gradio, Boto3, Docker, EC2, and CloudFront, with IAM permissions and persistent usage limits.

My biggest lesson: building an AI application means connecting the model, evidence, validation, and deployment into one reliable workflow.

Architecture and code: https://github.com/dhaval-mistry/QueryQuest
Try it: https://d2rof5vhi9w78g.cloudfront.net

What would you add next to a research assistant like this?

#GenerativeAI #AWS #AmazonBedrock #AIEngineering #Python

---

Suggested image alt text: Illustrated QueryQuest architecture. A user accesses CloudFront and a Gradio app running behind Nginx in Docker on EC2. The Planner and Writer call Claude on Amazon Bedrock; Search calls AgentCore Web Search for evidence from public web sources. The app validates article structure and source IDs, then returns a report with source links. An IAM role grants permissions, SQLite tracks usage counters, and GitHub supplies deployment source code.
