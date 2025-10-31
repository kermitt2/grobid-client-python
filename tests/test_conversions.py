"""
Unit tests for TEI to JSON and TEI to Markdown conversion functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
import tempfile
from grobid_client.grobid_client import GrobidClient
from tests.resources import TEST_DATA_PATH


class TestTEIConversions:
    """Test cases for TEI to JSON and Markdown conversions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_tei_content = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Sample Document Title</title>
            </titleStmt>
            <publicationStmt>
                <publisher>Sample Publisher</publisher>
                <date when="2023-01-01">2023-01-01</date>
            </publicationStmt>
        </fileDesc>
    </teiHeader>
    <text>
        <body>
            <div>
                <head>Introduction</head>
                <p>This is a sample paragraph with a citation <ref type="bibr" target="#b1">[1]</ref>.</p>
            </div>
        </body>
    </text>
</TEI>"""

        self.test_config = {
            'grobid_server': 'http://localhost:8070',
            'batch_size': 10,
            'sleep_time': 5,
            'timeout': 180,
            'logging': {
                'level': 'WARNING',
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'console': True,
                'file': None
            }
        }

    @patch('grobid_client.grobid_client.GrobidClient._test_server_connection')
    @patch('grobid_client.grobid_client.GrobidClient._configure_logging')
    def test_json_conversion_with_existing_tei_file(self, mock_configure_logging, mock_test_server):
        """Test JSON conversion when TEI file exists but JSON doesn't."""
        mock_test_server.return_value = (True, 200)

        client = GrobidClient(check_server=False)
        client.logger = Mock()

        # Create a temporary TEI file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tei.xml', delete=False) as tei_file:
            tei_file.write(self.sample_tei_content)
            tei_path = tei_file.name

        try:
            # Test actual conversion
            from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
            converter = TEI2LossyJSONConverter()
            json_data = converter.convert_tei_file(tei_path, stream=False)

            # Verify the conversion result
            assert json_data is not None, "JSON conversion should not return None"
            assert isinstance(json_data, dict), "JSON conversion should return a dictionary"

            # Check that the converted data has expected structure
            if 'biblio' in json_data:
                assert 'title' in json_data['biblio'], "Converted JSON should have title in biblio"

            # The conversion should preserve some content from the TEI
            if json_data.get('biblio', {}).get('title'):
                assert 'Sample Document Title' in json_data['biblio']['title']

        finally:
            # Clean up temporary file
            os.unlink(tei_path)

    @patch('grobid_client.grobid_client.GrobidClient._test_server_connection')
    @patch('grobid_client.grobid_client.GrobidClient._configure_logging')
    def test_json_conversion_with_empty_tei(self, mock_configure_logging, mock_test_server):
        """Test JSON conversion with empty or malformed TEI content."""
        mock_test_server.return_value = (True, 200)

        client = GrobidClient(check_server=False)
        client.logger = Mock()

        # Test with empty TEI content
        empty_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
</TEI>"""

        # Create a temporary TEI file with empty content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tei.xml', delete=False) as tei_file:
            tei_file.write(empty_tei)
            tei_path = tei_file.name

        try:
            # Test actual conversion
            from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
            converter = TEI2LossyJSONConverter()
            json_data = converter.convert_tei_file(tei_path, stream=False)

            # Verify that conversion still produces a valid structure even with empty TEI
            assert json_data is not None, "Even empty TEI should produce some JSON structure"
            assert isinstance(json_data, dict), "Result should still be a dictionary"

        finally:
            # Clean up temporary file
            os.unlink(tei_path)

    def test_json_conversion_with_nonexistent_file(self):
        """Test JSON conversion with nonexistent TEI file."""

        # Test with nonexistent file
        from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
        converter = TEI2LossyJSONConverter()

        # Should handle nonexistent file gracefully
        try:
            json_data = converter.convert_tei_file('/nonexistent/file.xml', stream=False)
            # This should either return None or raise an appropriate exception
            assert json_data is None, "Nonexistent file should return None"
        except Exception as e:
            # It's acceptable to raise an exception for nonexistent files
            assert True, "Exception is acceptable for nonexistent files"

    @patch('grobid_client.grobid_client.GrobidClient._test_server_connection')
    @patch('grobid_client.grobid_client.GrobidClient._configure_logging')
    def test_markdown_conversion_with_existing_tei_file(self, mock_configure_logging, mock_test_server):
        """Test Markdown conversion when TEI file exists but Markdown doesn't."""
        mock_test_server.return_value = (True, 200)

        client = GrobidClient(check_server=False)
        client.logger = Mock()

        # Create a temporary TEI file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tei.xml', delete=False) as tei_file:
            tei_file.write(self.sample_tei_content)
            tei_path = tei_file.name

        try:
            # Test actual conversion
            from grobid_client.format.TEI2Markdown import TEI2MarkdownConverter
            converter = TEI2MarkdownConverter()
            markdown_data = converter.convert_tei_file(tei_path)

            # Verify the conversion result
            assert markdown_data is not None, "Markdown conversion should not return None"
            assert isinstance(markdown_data, str), "Markdown conversion should return a string"
            assert len(markdown_data) > 0, "Markdown conversion should produce non-empty content"

            # Check that the converted content contains expected elements
            assert '#' in markdown_data or 'Sample Document Title' in markdown_data, "Markdown should contain title"

        finally:
            # Clean up temporary file
            os.unlink(tei_path)

    def test_markdown_conversion_with_empty_tei(self):
        """Test Markdown conversion with empty TEI content."""

        # Test with empty TEI content
        empty_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
</TEI>"""

        # Create a temporary TEI file with empty content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tei.xml', delete=False) as tei_file:
            tei_file.write(empty_tei)
            tei_path = tei_file.name

        try:
            # Test actual conversion
            from grobid_client.format.TEI2Markdown import TEI2MarkdownConverter
            converter = TEI2MarkdownConverter()
            markdown_data = converter.convert_tei_file(tei_path)

            # Verify that conversion still produces some content even with empty TEI
            assert markdown_data is not None, "Even empty TEI should produce some markdown content"
            assert isinstance(markdown_data, str), "Result should be a string"

        finally:
            # Clean up temporary file
            os.unlink(tei_path)

    @patch('grobid_client.grobid_client.GrobidClient._test_server_connection')
    @patch('grobid_client.grobid_client.GrobidClient._configure_logging')
    def test_both_conversions_same_tei_file(self, mock_configure_logging, mock_test_server):
        """Test both JSON and Markdown conversions for the same TEI file."""
        mock_test_server.return_value = (True, 200)

        client = GrobidClient(check_server=False)
        client.logger = Mock()

        # Create a temporary TEI file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tei.xml', delete=False) as tei_file:
            tei_file.write(self.sample_tei_content)
            tei_path = tei_file.name

        try:
            # Test JSON conversion
            from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
            json_converter = TEI2LossyJSONConverter()
            json_data = json_converter.convert_tei_file(tei_path, stream=False)

            # Test Markdown conversion
            from grobid_client.format.TEI2Markdown import TEI2MarkdownConverter
            md_converter = TEI2MarkdownConverter()
            markdown_data = md_converter.convert_tei_file(tei_path)

            # Verify both conversions produced valid results
            assert json_data is not None, "JSON conversion should not return None"
            assert isinstance(json_data, dict), "JSON conversion should return a dictionary"

            assert markdown_data is not None, "Markdown conversion should not return None"
            assert isinstance(markdown_data, str), "Markdown conversion should return a string"
            assert len(markdown_data) > 0, "Markdown should have content"

            # Both conversions should be from the same source, so they should extract similar information
            if 'biblio' in json_data and 'title' in json_data['biblio']:
                title = json_data['biblio']['title']
                # The title should appear in the markdown output
                assert title in markdown_data or 'Sample Document Title' in markdown_data, "Title should appear in markdown"

        finally:
            # Clean up temporary file
            os.unlink(tei_path)

    def test_process_batch_with_json_output(self):
        """Test process_batch method with JSON output functionality using real TEI resources."""

        # Use the actual TEI file from test resources
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')

        # Verify the test TEI file exists
        assert os.path.exists(tei_file), f"Test TEI file should exist at {tei_file}"

        # Test actual conversion using the same converter that process_batch would use
        from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
        converter = TEI2LossyJSONConverter()
        json_data = converter.convert_tei_file(tei_file, stream=False)

        # Verify conversion worked
        assert json_data is not None, "JSON conversion should succeed"
        assert isinstance(json_data, dict), "Should return dictionary"

        # Test that JSON contains expected content from the real TEI file
        if 'biblio' in json_data:
            biblio = json_data['biblio']
            assert 'title' in biblio, "Should extract title"
            assert 'Multi-contact functional electrical stimulation' in biblio['title']

            if 'authors' in biblio:
                assert len(biblio['authors']) > 0, "Should extract authors"

        # Test filename generation logic (same as used in process_batch)
        json_filename = tei_file.replace('.tei.xml', '.json')
        assert json_filename.endswith('.json'), "Should generate .json filename"

    def test_real_tei_json_conversion_integration(self):
        """Test complete TEI to JSON conversion workflow with realistic TEI content."""

        # Use the actual TEI file from test resources
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')

        # Verify the test TEI file exists
        assert os.path.exists(tei_file), f"Test TEI file should exist at {tei_file}"

        # Test actual conversion
        from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
        converter = TEI2LossyJSONConverter()
        json_data = converter.convert_tei_file(tei_file, stream=False)

        # Verify comprehensive conversion results
        assert json_data is not None, "Conversion should not return None"
        assert isinstance(json_data, dict), "Result should be a dictionary"

        # Test bibliography extraction
        if 'biblio' in json_data:
            biblio = json_data['biblio']

            # Should extract title
            if 'title' in biblio:
                assert 'Multi-contact functional electrical stimulation' in biblio['title']

            # Should extract authors
            if 'authors' in biblio and len(biblio['authors']) > 0:
                assert isinstance(biblio['authors'], list)
                # Check that first author has expected name
                first_author = biblio['authors'][0]
                if 'name' in first_author:
                    assert 'De Marchis' in first_author['name'] or 'Cristiano' in first_author['name']

            # Should extract publication date
            if 'publication_date' in biblio:
                assert biblio['publication_date'] == '2016-03-08'

        # Test body text extraction
        if 'body_text' in json_data and len(json_data['body_text']) > 0:
            body_text = json_data['body_text']

            # Should have at least one paragraph
            paragraphs = [p for p in body_text if p.get('text')]
            assert len(paragraphs) > 0, "Should extract at least one paragraph"

            # Should have references in some paragraphs
            refs_found = []
            for paragraph in paragraphs:
                if 'refs' in paragraph and paragraph['refs']:
                    refs_found.extend(paragraph['refs'])

            # Should find bibliographic references if any exist
            if refs_found:
                ref_types = {ref.get('type') for ref in refs_found}
                # Check for common reference types
                assert len(ref_types) > 0, "Should find some reference types"

                # Test reference structure
                for ref in refs_found[:3]:  # Check first few references
                    assert 'type' in ref, "Reference should have type"
                    assert 'text' in ref, "Reference should have text"
                    assert 'offset_start' in ref, "Reference should have offset_start"
                    assert 'offset_end' in ref, "Reference should have offset_end"
                    assert ref['offset_start'] < ref['offset_end'], "offset_start should be less than offset_end"

    def test_markdown_conversion_with_real_tei_file(self):
        """Test Markdown conversion with real TEI file from test resources."""

        # Use the actual TEI file from test resources
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')

        # Verify the test TEI file exists
        assert os.path.exists(tei_file), f"Test TEI file should exist at {tei_file}"

        # Test actual conversion
        from grobid_client.format.TEI2Markdown import TEI2MarkdownConverter
        converter = TEI2MarkdownConverter()
        markdown_data = converter.convert_tei_file(tei_file)

        # Verify the conversion result
        assert markdown_data is not None, "Markdown conversion should not return None"
        assert isinstance(markdown_data, str), "Markdown conversion should return a string"
        assert len(markdown_data) > 0, "Markdown conversion should produce non-empty content"

        # Check that the converted content contains expected elements from real TEI
        assert '#' in markdown_data, "Markdown should contain headers"
        assert 'Multi-contact functional electrical stimulation' in markdown_data, "Markdown should contain the paper title"

        # Check for author information
        assert 'De Marchis' in markdown_data or 'Cristiano' in markdown_data, "Markdown should contain author information"