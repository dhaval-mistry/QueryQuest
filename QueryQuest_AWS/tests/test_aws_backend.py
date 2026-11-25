"""Offline AWS contract and workflow tests; no credentials or network needed."""

import json
import os
import unittest
from unittest.mock import patch

import boto3
from botocore.stub import ANY, Stubber
from pydantic import ValidationError

from config import bedrock_model
from config import AWSConfigurationError, require_research_credentials
from botocore.exceptions import PartialCredentialsError, ProfileNotFound
from QQagents.planner_agent import WebSearchPlan, create_planner_agent
from QQagents.search_agent import create_search_agent
from QQagents.writer_agent import ResearchArticle
from queryquest_workflow import format_article, run_research, research_steps
from services.bedrock_agent import BedrockAgent, tool_schema, normalize_containers
from services.email_sender import send_email


def client(service):
    return boto3.client(service, region_name="us-east-1",
                        aws_access_key_id="testing", aws_secret_access_key="testing")


def structured_response(data, stop_reason="tool_use"):
    return {
        "output": {"message": {"role": "assistant", "content": [{"toolUse": {
            "toolUseId": "result-1", "name": "submit_result", "input": data,
        }}]}},
        "stopReason": stop_reason,
        "usage": {"inputTokens": 10, "outputTokens": 10, "totalTokens": 20},
        "metrics": {"latencyMs": 1},
    }


ARTICLE = {
    "title": "Research", "summary": "Summary", "conclusion": "Conclusion",
    "sections": [{"heading": "Evidence", "paragraphs": [{"text": "A finding", "source_ids": [1]}]}],
}


class AwsBackendTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "SystemRoot": os.getenv("SystemRoot", "C:\\Windows"),
            "BEDROCK_MODEL": "us.amazon.nova-lite-v1:0", "HOW_MANY_SEARCHES": "2",
            "BEDROCK_MAX_TOKENS": "4096", "MAX_SEARCHES_PER_RUN": "2",
            "AWS_SEARCH_MAX_RESULTS": "5", "EMAIL_ADDRESS": "sender@example.com",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        # Workflow tests stub AWS calls and must never look up real credentials.
        credentials = patch("queryquest_workflow.require_research_credentials")
        credentials.start()
        self.addCleanup(credentials.stop)

    def test_bedrock_token_does_not_replace_search_credentials(self):
        with patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "test-token"}), \
                patch("config.boto3.Session") as session, \
                patch("queryquest_workflow.require_research_credentials", wraps=require_research_credentials), \
                patch("queryquest_workflow.create_planner_agent") as planner:
            session.return_value.get_credentials.return_value = None
            with self.assertRaisesRegex(AWSConfigurationError, "AWS Web Search needs IAM credentials"):
                run_research("Question")
            planner.assert_not_called()

    def test_missing_profile_and_partial_credentials_explain_setup(self):
        for error in (ProfileNotFound(profile="missing"), PartialCredentialsError(provider="env", cred_var="AWS_SECRET_ACCESS_KEY")):
            with self.subTest(error=type(error).__name__), patch("config.boto3.Session") as session:
                session.return_value.get_credentials.side_effect = error
                with self.assertRaisesRegex(AWSConfigurationError, "AWS_PROFILE"):
                    require_research_credentials()

    def test_iam_credentials_allow_research_to_proceed(self):
        with patch("config.boto3.Session") as session:
            session.return_value.get_credentials.return_value = object()
            require_research_credentials()

    def test_converse_validates_structured_output_and_request(self):
        runtime = client("bedrock-runtime")
        plan = {"searches": [{"query": "AWS research", "reason": "Find documentation"}]}
        with Stubber(runtime) as stub, patch("services.bedrock_agent.aws_client", return_value=runtime):
            stub.add_response("converse", structured_response(plan), {
                "modelId": "us.amazon.nova-lite-v1:0", "system": ANY, "messages": ANY,
                "inferenceConfig": {"maxTokens": 4096, "temperature": 0},
                "toolConfig": {
                    "tools": [{"toolSpec": {
                        "name": "submit_result", "description": ANY,
                        "inputSchema": {"json": tool_schema(WebSearchPlan)},
                    }}], "toolChoice": {"tool": {"name": "submit_result"}},
                },
            })
            result = create_planner_agent().run("Research AWS")
            self.assertIsInstance(result, WebSearchPlan)
            self.assertEqual(result.searches[0].query, "AWS research")
            stub.assert_no_pending_responses()

    def test_nested_schema_has_no_unresolved_references(self):
        schema = tool_schema(ResearchArticle)
        self.assertEqual(set(schema), {"type", "properties", "required"})
        self.assertIn("title", schema["properties"])
        self.assertNotIn("$ref", json.dumps(schema))
        self.assertNotIn("$defs", json.dumps(schema))

    def test_incomplete_and_invalid_model_output_are_rejected(self):
        agent = BedrockAgent("Test", "Plan", "us.amazon.nova-lite-v1:0", WebSearchPlan)
        runtime = client("bedrock-runtime")
        with Stubber(runtime) as stub, patch("services.bedrock_agent.aws_client", return_value=runtime):
            stub.add_response("converse", structured_response({}, "max_tokens"))
            with self.assertRaisesRegex(ValueError, "max_tokens"):
                agent.run("Question")
            stub.add_response("converse", structured_response({"searches": [{"query": "x" * 201, "reason": "test"}]}))
            stub.add_response("converse", structured_response({"searches": [{"query": "x" * 201, "reason": "test"}]}))
            with self.assertRaises(ValidationError):
                agent.run("Question")

    def test_writer_accepts_json_encoded_sections_without_another_model_call(self):
        runtime = client("bedrock-runtime")
        data = {**ARTICLE, "sections": json.dumps(ARTICLE["sections"])}
        agent = BedrockAgent("Writer", "Use evidence", "test-model", ResearchArticle)
        with Stubber(runtime) as stub, patch("services.bedrock_agent.aws_client", return_value=runtime):
            stub.add_response("converse", structured_response(data))
            result = agent.run("Evidence")
            self.assertEqual(result.sections[0].paragraphs[0].source_ids, [1])
            stub.assert_no_pending_responses()

    def test_nested_container_repair_preserves_text_and_required_citations(self):
        schema = tool_schema(ResearchArticle)
        data = {**ARTICLE, "title": '["This remains a title"]', "sections": [{
            "heading": "Evidence", "paragraphs": json.dumps([{"text": '{"text":"unchanged"}', "source_ids": "[1]"}]),
        }]}
        article = ResearchArticle.model_validate(normalize_containers(data, schema))
        self.assertEqual(article.title, '["This remains a title"]')
        self.assertEqual(article.sections[0].paragraphs[0].text, '{"text":"unchanged"}')
        data["sections"][0]["paragraphs"] = '[{"text":"Missing citation"}]'
        with self.assertRaises(ValidationError):
            ResearchArticle.model_validate(normalize_containers(data, schema))

    def test_invalid_output_retries_only_the_same_agent_once(self):
        runtime = client("bedrock-runtime")
        agent = BedrockAgent("Writer", "Use evidence", "test-model", ResearchArticle)
        with Stubber(runtime) as stub, patch("services.bedrock_agent.aws_client", return_value=runtime):
            stub.add_response("converse", structured_response({**ARTICLE, "sections": "not JSON"}))
            stub.add_response("converse", structured_response(ARTICLE))
            self.assertEqual(agent.run("Evidence").title, "Research")
            stub.assert_no_pending_responses()

    def test_search_preserves_evidence_and_removes_unusable_sources(self):
        search = client("bedrock-agentcore")
        with Stubber(search) as stub, patch("QQagents.search_agent.aws_client", return_value=search):
            stub.add_response("invoke_web_search", {"results": [
                {"title": "AWS", "url": "https://aws.amazon.com/", "text": "Retrieved evidence"},
                {"url": "https://aws.amazon.com/", "text": "Duplicate"},
                {"url": "javascript:alert(1)", "text": "Unsafe link"},
                {"text": "Missing URL"},
            ]}, {"webSearchId": "web-search.v1", "searchQuery": "AWS", "maxResults": 5})
            result = create_search_agent().run("AWS")
            self.assertEqual(result.findings, ["Retrieved evidence"])
            self.assertEqual(result.sources[0].url, "https://aws.amazon.com/")
            stub.assert_no_pending_responses()

    def test_search_limits_are_checked_before_calling_aws(self):
        with patch("QQagents.search_agent.aws_client") as factory:
            for query in ("", "x" * 201):
                with self.assertRaises(ValueError):
                    create_search_agent().run(query)
            factory.assert_not_called()

    def test_ses_preserves_mime_alternatives_and_recipient(self):
        from email import policy
        from email.parser import BytesParser
        ses = client("sesv2")
        with Stubber(ses) as stub, patch("services.email_sender.aws_client", return_value=ses):
            stub.add_response("send_email", {"MessageId": "test"}, {
                "FromEmailAddress": "sender@example.com",
                "Destination": {"ToAddresses": ["recipient@example.com"]},
                "Content": {"Raw": {"Data": ANY}},
            })
            with patch.object(ses, "send_email", wraps=ses.send_email) as send:
                send_email("Report", "Plain evidence", "recipient@example.com", "<p>HTML evidence</p>")
                message = BytesParser(policy=policy.default).parsebytes(send.call_args.kwargs["Content"]["Raw"]["Data"])
                self.assertIn("Plain evidence", message.get_body(preferencelist=("plain",)).get_content())
                self.assertIn("HTML evidence", message.get_body(preferencelist=("html",)).get_content())
            stub.assert_no_pending_responses()

    def test_full_research_flow_keeps_source_ids(self):
        runtime, search = client("bedrock-runtime"), client("bedrock-agentcore")
        with Stubber(runtime) as models, Stubber(search) as searches, \
                patch("services.bedrock_agent.aws_client", return_value=runtime), \
                patch("QQagents.search_agent.aws_client", return_value=search):
            models.add_response("converse", structured_response({"searches": [
                {"query": "AWS one", "reason": "one"}, {"query": "AWS two", "reason": "two"},
            ]}))
            models.add_response("converse", structured_response(ARTICLE))
            for query in ("AWS one", "AWS two"):
                searches.add_response("invoke_web_search", {"results": [
                    {"title": "Source", "url": "https://example.com/", "text": "Evidence"},
                ]}, {"webSearchId": "web-search.v1", "searchQuery": query, "maxResults": 5})
            updates = list(research_steps("Question"))
            self.assertEqual([item.stage for item in updates], ["planner", "search", "search", "writer", "complete"])
            self.assertIn("query 1 of 2", updates[1].detail)
            article, sources, completed, planned = updates[-1].result
            self.assertEqual((completed, planned, len(sources)), (2, 2, 1))
            self.assertIn("[1]", format_article(article, sources, completed, planned))
            article.sections[0].paragraphs[0].source_ids = [99]
            with self.assertRaisesRegex(ValueError, "unknown source"):
                format_article(article, sources, completed, planned)
            models.assert_no_pending_responses()
            searches.assert_no_pending_responses()

    def test_no_evidence_prevents_writing(self):
        with patch("queryquest_workflow.create_planner_agent") as planner, \
                patch("queryquest_workflow.create_search_agent") as search, \
                patch("queryquest_workflow.create_writer_agent") as writer:
            planner.return_value.run.return_value = WebSearchPlan(searches=[{"query": "AWS", "reason": "test"}])
            search.return_value.run.return_value.sources = []
            search.return_value.run.return_value.findings = []
            with self.assertRaisesRegex(ValueError, "no usable sources"):
                run_research("Question")
            writer.assert_not_called()

    def test_native_default_and_role_model_override(self):
        del os.environ["BEDROCK_MODEL"]
        self.assertEqual(bedrock_model("planner"), "us.anthropic.claude-sonnet-4-6")
        os.environ["BEDROCK_WRITER_MODEL"] = "us.amazon.nova-pro-v1:0"
        self.assertEqual(bedrock_model("writer"), "us.amazon.nova-pro-v1:0")
        os.environ["BEDROCK_MODEL"] = "openai.gpt-oss-120b"
        with self.assertRaisesRegex(ValueError, "Converse model"):
            bedrock_model("planner")


if __name__ == "__main__":
    unittest.main()
