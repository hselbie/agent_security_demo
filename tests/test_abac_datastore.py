import unittest
import os
import json
from unittest.mock import MagicMock, patch

# Assuming the project root is on the Python path for imports
from abac_demo.tools.datastore import get_datastore_content

class TestABACDatastore(unittest.TestCase):

    def setUp(self):
        self.mock_tool_context = MagicMock()
        self.data_dir = "abac_demo/data"
        os.makedirs(self.data_dir, exist_ok=True)

        self.marketing_full_data = {"budget": 100000, "campaigns": ["Q1_Launch", "Holiday_Promo"]}
        self.marketing_limited_data = {"campaigns": ["Q1_Launch", "Holiday_Promo"]}
        self.sales_full_data = {"value": 500000, "deals": ["Enterprise_A", "SMB_B"]}
        self.sales_limited_data = {"deals": ["Enterprise_A", "SMB_B"]}

        with open(os.path.join(self.data_dir, "marketing_data.json"), "w") as f:
            json.dump({"full": self.marketing_full_data, "limited": self.marketing_limited_data}, f)
        with open(os.path.join(self.data_dir, "sales_data.json"), "w") as f:
            json.dump({"full": self.sales_full_data, "limited": self.sales_limited_data}, f)

    def tearDown(self):
        os.remove(os.path.join(self.data_dir, "marketing_data.json"))
        os.remove(os.path.join(self.data_dir, "sales_data.json"))
        os.rmdir(self.data_dir)

    def test_get_marketing_manager_access(self):
        result = get_datastore_content("marketing", "manager", self.mock_tool_context)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], self.marketing_full_data)

    def test_get_marketing_employee_access(self):
        result = get_datastore_content("marketing", "employee", self.mock_tool_context)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], self.marketing_limited_data)

    def test_get_sales_manager_access(self):
        result = get_datastore_content("sales", "manager", self.mock_tool_context)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], self.sales_full_data)

    def test_get_sales_employee_access(self):
        result = get_datastore_content("sales", "employee", self.mock_tool_context)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], self.sales_limited_data)

    def test_invalid_access_level(self):
        result = get_datastore_content("marketing", "invalid_role", self.mock_tool_context)
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid access level", result["message"])

    @patch('abac_demo.tools.datastore.json.load')
    def test_json_decode_error(self, mock_json_load):
        mock_json_load.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        result = get_datastore_content("marketing", "manager", self.mock_tool_context)
        self.assertEqual(result["status"], "error")
        self.assertIn("Error reading datastore 'marketing': Invalid JSON format.", result["message"])

    @patch('abac_demo.tools.datastore.open')
    def test_file_not_found_error(self, mock_open):
        mock_open.side_effect = FileNotFoundError
        result = get_datastore_content("non_existent_datastore", "manager", self.mock_tool_context)
        self.assertEqual(result["status"], "error")
        self.assertIn("Datastore 'non_existent_datastore' not found.", result["message"])

    def test_unexpected_exception(self):
        with patch('abac_demo.tools.datastore.json.load') as mock_json_load:
            mock_json_load.side_effect = Exception("Generic error")
            result = get_datastore_content("marketing", "manager", self.mock_tool_context)
            self.assertEqual(result["status"], "error")
            self.assertIn("Generic error", result["message"])

if __name__ == '__main__':
    unittest.main()
