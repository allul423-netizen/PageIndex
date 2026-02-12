import sys
import os
import unittest
import asyncio
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pageindex.page_index import fix_inverted_indices
from pageindex.utils import generate_summaries_for_structure

class TestDeepSeekAdaptations(unittest.TestCase):
    def test_fix_inverted_indices(self):
        structure = [
            {
                "title": "Normal Node",
                "start_index": 1,
                "end_index": 5,
                "nodes": [
                    {
                        "title": "Inverted Node",
                        "start_index": 4,
                        "end_index": 3,
                        "nodes": []
                    }
                ]
            }
        ]
        
        fixed_structure = fix_inverted_indices(structure)
        
        # Verify the fix: end_index should be set to start_index (4)
        self.assertEqual(fixed_structure[0]["nodes"][0]["end_index"], 4)
        # Verify other nodes remain unchanged
        self.assertEqual(fixed_structure[0]["start_index"], 1)
        self.assertEqual(fixed_structure[0]["end_index"], 5)

    def test_generate_summaries_skips_existing(self):
        structure = [
            {
                "title": "Node with Summary",
                "summary": "Existing summary",
                "text": "Some text",
                "nodes": []
            },
            {
                "title": "Node without Summary",
                "text": "Some other text",
                "nodes": []
            } 
        ]
        
        # Mock generate_node_summary to return "New Summary"
        async def async_mock(node, model=None):
            return "New Summary"

        with patch('pageindex.utils.generate_node_summary', side_effect=async_mock) as mock_generate:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(generate_summaries_for_structure(structure))
            loop.close()
            
            # Check if summary was preserved for first node
            self.assertEqual(result[0]["summary"], "Existing summary")
            # Check if summary was generated for second node
            self.assertEqual(result[1]["summary"], "New Summary")
            
            # Check that generate_node_summary was called exactly once
            mock_generate.assert_called_once()
            # Verify the call arguments 
            args, _ = mock_generate.call_args
            self.assertEqual(args[0]["title"], "Node without Summary")

if __name__ == '__main__':
    unittest.main()
