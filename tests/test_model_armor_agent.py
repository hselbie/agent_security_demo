import unittest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types as genai_types
from google.cloud import modelarmor_v1

# Assuming the project root is on the Python path for imports
from model_armor_demo.agent import model_armor_callback

class TestModelArmorAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_callback_context = MagicMock(spec=CallbackContext)
        self.mock_llm_request = MagicMock(spec=LlmRequest)
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="test prompt")])]

    @patch('model_armor_demo.agent.modelarmor_v1.ModelArmorAsyncClient')
    @patch('model_armor_demo.agent.GOOGLE_CLOUD_PROJECT_ID', 'test-project')
    async def test_model_armor_blocks_sensitive_content(self, MockModelArmorAsyncClient):
        mock_client_instance = MockModelArmorAsyncClient.return_value
        # Mock the response structure
        mock_response = MagicMock()
        # 2 represents MATCH (or BLOCKED depending on interpretation, matching the agent logic)
        mock_response.sanitization_result.filter_match_state = 2 
        
        # Configure sanitize_user_prompt as an AsyncMock
        mock_client_instance.sanitize_user_prompt = AsyncMock(return_value=mock_response)

        response = await model_armor_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, LlmResponse)
        self.assertIn("Blocked by Model Armor", response.content.parts[0].text)
        mock_client_instance.sanitize_user_prompt.assert_called_once()

    @patch('model_armor_demo.agent.modelarmor_v1.ModelArmorAsyncClient')
    @patch('model_armor_demo.agent.GOOGLE_CLOUD_PROJECT_ID', 'test-project')
    async def test_model_armor_allows_benign_content(self, MockModelArmorAsyncClient):
        mock_client_instance = MockModelArmorAsyncClient.return_value
        mock_response = MagicMock()
        # 1 represents NO_MATCH (or ALLOWED)
        mock_response.sanitization_result.filter_match_state = 1
        
        # Configure sanitize_user_prompt as an AsyncMock
        mock_client_instance.sanitize_user_prompt = AsyncMock(return_value=mock_response)

        response = await model_armor_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNone(response)
        mock_client_instance.sanitize_user_prompt.assert_called_once()

    @patch('model_armor_demo.agent.modelarmor_v1.ModelArmorAsyncClient')
    @patch('model_armor_demo.agent.GOOGLE_CLOUD_PROJECT_ID', 'test-project')
    async def test_model_armor_handles_api_error(self, MockModelArmorAsyncClient):
        mock_client_instance = MockModelArmorAsyncClient.return_value
        # Configure sanitize_user_prompt as an AsyncMock that raises an exception
        mock_client_instance.sanitize_user_prompt = AsyncMock(side_effect=Exception("API error"))

        response = await model_armor_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, LlmResponse)
        self.assertIn("An error occurred during safety check", response.content.parts[0].text)
        mock_client_instance.sanitize_user_prompt.assert_called_once()

    @patch('model_armor_demo.agent.GOOGLE_CLOUD_PROJECT_ID', '')
    async def test_model_armor_with_empty_project_id(self):
        # When project ID is empty, it should log a warning and return None
        response = await model_armor_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNone(response)

    @patch('model_armor_demo.agent.modelarmor_v1.ModelArmorAsyncClient')
    @patch('model_armor_demo.agent.GOOGLE_CLOUD_PROJECT_ID', 'test-project')
    async def test_model_armor_with_empty_prompt(self, MockModelArmorAsyncClient):
        mock_client_instance = MockModelArmorAsyncClient.return_value
        # Need to mock this even if we expect it not to be called, to prevent attribute errors if logic fails
        mock_client_instance.sanitize_user_prompt = AsyncMock() 
        
        self.mock_llm_request.contents = [genai_types.Content(parts=[genai_types.Part(text="")])]
        response = await model_armor_callback(self.mock_callback_context, self.mock_llm_request)
        self.assertIsNone(response)
        # Should not call API if prompt is empty
        mock_client_instance.sanitize_user_prompt.assert_not_called()

if __name__ == '__main__':
    unittest.main()
