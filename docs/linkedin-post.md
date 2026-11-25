# LinkedIn post

Attach `assets/queryquest-architecture.png` as the image, then paste the text below.

---

I built QueryQuest to turn a question into a research report with clickable sources.

Then I built it two ways:

🟢 GPT + OpenAI web search, using the OpenAI Agents SDK.
🟠 Claude on Amazon Bedrock + AWS AgentCore Web Search, using Boto3.

Both follow the same flow: plan → search → write → validate citations.

The AWS version is now live with Docker, EC2, CloudFront HTTPS, IAM roles, and persistent usage limits.

My biggest lesson: changing the model is only part of the work. Authentication, structured outputs, and deployment deserve just as much attention.

Explore the architecture: https://dhaval-mistry.github.io/QueryQuest/
Code: https://github.com/dhaval-mistry/QueryQuest

Which approach would you choose for your next AI application—and why?

#GenerativeAI #AWS #AmazonBedrock #OpenAI #Python

---

Suggested image alt text: QueryQuest architecture comparing two research workflows. The GPT route uses the OpenAI Agents SDK, GPT, and OpenAI WebSearchTool. The AWS route uses Boto3, Claude on Amazon Bedrock, and direct AgentCore Web Search calls. Both plan research, search, write, and validate reports with source links. The AWS app is hosted through CloudFront, Nginx, Docker, and EC2.
