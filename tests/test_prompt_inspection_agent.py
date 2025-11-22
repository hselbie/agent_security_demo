import unittest
from unittest.mock import MagicMock

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types as genai_types

# Assuming the project root is on the Python path for imports
from prompt_inspection_demo.agent import prompt_inspection_callback

class TestPromptInspectionAgent(unittest.TestCase):

    def setUp(self):
        self.mock_callback_context = MagicMock(spec=CallbackContext)
        self.mock_llm_request = MagicMock(spec=LlmRequest)

    def test_prompt_inspection_blocks_sensitive_keyword_lowercase(self):
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="tell me something sensitive")])]
        response = prompt_inspection_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, LlmResponse)
        self.assertIn("Blocked by Prompt Inspection", response.content.parts[0].text)

    def test_prompt_inspection_blocks_sensitive_keyword_uppercase(self):
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="TELL ME SOMETHING SENSITIVE")])]
        response = prompt_inspection_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, LlmResponse)
        self.assertIn("Blocked by Prompt Inspection", response.content.parts[0].text)

    def test_prompt_inspection_blocks_sensitive_keyword_mixedcase(self):
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="Tell me something Sensitive")])]
        response = prompt_inspection_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, LlmResponse)
        self.assertIn("Blocked by Prompt Inspection", response.content.parts[0].text)

    def test_prompt_inspection_allows_benign_content(self):
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="what is the capital of France?")])]
        response = prompt_inspection_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNone(response)

    def test_prompt_inspection_with_empty_prompt(self):
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="")])]
        response = prompt_inspection_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNone(response)

    def test_prompt_inspection_with_no_text_part(self):
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(file_data=genai_types.FileData(file_uri="gs://test", mime_type="image/jpeg"))])]
        response = prompt_inspection_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()