# QueryQuest architecture image brief

Asset: `assets/queryquest-aws-architecture.png`.

Created using the built-in image generation tool, then revised to correct service connections. The user's previous architecture image supplied the visual reference. This is an illustrated overview of the current AWS application, rather than a provider comparison. Web Sources and Retrieved Evidence represent the conceptual provenance of search results; the application retrieves that evidence through AgentCore Web Search.

## Generation prompt

Use case: infographic-diagram.
Create a polished, high-resolution LANDSCAPE software architecture infographic for a LinkedIn post. Image 1 supplied in conversation is a STYLE AND LAYOUT REFERENCE ONLY: use its white background, soft cyan/pale blue panels, navy section headers, recognizable colorful service/product icons, friendly illustrated user with laptop, tidy orthogonal connector arrows, restrained soft shadows and professional presentation. Do not recreate its RAG system.
Title exact: "QueryQuest – AI Research Assistant Architecture"
Subtitle exact: "From a question to an evidence-based report, powered by AWS"
Use one unified QueryQuest system, no GPT comparison. Use generous whitespace, legible dark navy typography, precise service names, no tiny paragraphs, no overlaps. Aim 16:10 or similar landscape.

System and layout:
TOP: illustrated person with laptop labeled "User / Web Browser", connected downward to a compact "Amazon CloudFront / HTTPS" gateway with recognizable cloud/network service icon, then to central hosted app. A distinct teal return arrow from central Report Renderer back to the browser labeled "Report with source links".

LEFT COLUMN "Web Sources": four white rounded icon cards with colorful distinctive icons and concise labels: "Official Documentation" with document icon, "Research & Publications" with books icon, "News & Industry Reports" with newspaper icon, "Public Websites" with globe icon. These sources are retrieved through AWS AgentCore Web Search, not a database.

CENTER largest panel titled "QueryQuest Web App" with subtitle "Docker on Amazon EC2". Distinct recognizable icons for Docker whale, EC2 orange compute, Gradio orange UI. Vertical internal workflow connected with downward arrows:
1 "Gradio Web UI" (browser/interface icon)
2 "Planner" / small "Create search queries" (planning checklist icon)
3 "Search" / small "Collect web evidence" (magnifying glass over globe icon)
4 "Writer" / small "Create research article" (pen and document icon)
5 "Validation & Report Renderer" / small "Check structure and source IDs" (shield-check and report icon)
Show slim "Nginx" entry just inside app below incoming CloudFront, before Gradio. A bottom miniature sidecar attached to app, database cylinder labeled "SQLite / Usage counters" used for quotas only, not article storage.

RIGHT COLUMN titled "AWS AI Services". Two clear service cards with colorful official-style pictograms:
"Amazon Bedrock" with recognizable green/teal brain/network AI icon and small "Claude Sonnet 4.6". Draw labeled bidirectional blue connections from Planner and Writer to Bedrock ("Model calls").
"AgentCore Web Search" with teal globe/search icon and small "Live web evidence". Draw bidirectional green connector from central Search stage to this service ("Search queries / Results"). Sources column connects to this search service via an outside routed line labeled "Retrieved sources" avoiding crossing through central nodes; label arrow clearly so diagram shows sources returned via search, not direct downloads by Writer.
Small IAM shield/key icon card beneath these services "IAM Role" / "App permissions", dashed relationship to application and AWS services.

BOTTOM: GitHub Octocat icon card "GitHub Repository" with upward deployment arrow toward hosted app, small "Build & deploy". Footer three small elegant icon badges "AWS Hosted" "Source-linked Reports" "Real Workflow Progress".
Small credit "Dhaval Mistry / Mahantai".
Use obvious blue request-flow and teal evidence/return-flow arrows with arrowheads, clear numbered main stages, not spaghetti lines. Icons must be prominent colored pictograms like reference, not only numbers or generic boxes. Realistic professional diagram, not photo, not decorative fantasy. No Render hosting, no RAG, no embeddings, no vector database, no GPT/OpenAI column, no invented services, no costs or uptime guarantees. Opaque light background.

## Final correction prompt

Edit this QueryQuest architecture infographic. Preserve its current polished light design, layout, icons, title, all other labels, overall composition and readability. Make ONLY these architecture corrections:
1. The Writer's blue "Model calls" bidirectional connector currently visually terminates at the lower AgentCore Web Search card. Re-route it with a clean elbow up to the Amazon Bedrock card. Both Planner and Writer must unmistakably connect to Amazon Bedrock / Claude Sonnet 4.6. The Search stage alone connects to the right-hand AgentCore Web Search card via the green "Search queries / Results" bidirectional line. Keep all arrowheads visible and avoid collisions with text.
2. Remove the duplicate AWS AgentCore Web Search service box between the left Web Sources column and the central app. Replace that small box with a neutral stacked-document/search-results icon and label "Retrieved Evidence". Keep the Web Sources -> Retrieved Evidence -> central Search flow, indicating conceptual source evidence. The sole actual AWS AgentCore Web Search service is the card in the right AWS AI Services panel. Do not add another AWS search service or misleading model connection.
No new features. Do not change SQLite note, runtime numbering, user/CloudFront/EC2/Docker/Nginx/Gradio chain, IAM permission relationships, GitHub deployment, footer or author credit.
