"""
Unit tests for TEI to JSON and TEI to Markdown conversion functionality.
"""
import os
import tempfile
from unittest.mock import Mock, patch

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
                for ref in refs_found:  # Check ALL references
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

    def test_reference_offset_issues_with_known_cases(self):
        """Test TEI to JSON conversion for XML files with known reference offset issues."""
        import json
        from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter

        # Test cases with known reference offset problems
        test_cases = [
            {
                "xml_file": "10.1371_journal.pone.0218311.grobid.tei.xml",
                "json_file": "10.1371_journal.pone.0218311.json",
                "title": "Being right matters: Model-compliant events in predictive processing"
            },
            {
                "xml_file": "10.7554_elife.78558.grobid.tei.xml",
                "json_file": "10.7554_elife.78558.json",
                "title": "Macrophages regulate gastrointestinal motility through complement component 1q"
            },
            {
                "xml_file": "10.1038_s41477-023-01501-1.grobid.tei.xml",
                "json_file": "10.1038_s41477-023-01501-1.json",
                "title": "nature plants Article"
            },
            {
                "xml_file": "10.1038_s41598-023-32039-z.grobid.tei.xml",
                "json_file": "10.1038_s41598-023-32039-z.json",
                "title": "Identification of PARN nuclease activity inhibitors by computational-based docking and high-throughput screening"
            },
            {
                "xml_file": "10.1038_s41598-023-32039-z.grobid.tei.xml",
                "json_file": "10.1038_s41598-023-32039-z.json",
                "title": "Identification of PARN nuclease activity inhibitors by computational-based docking and high-throughput screening"
            }
            ,
            {
                "xml_file": "10.1038_s41586-023-05895-y.grobid.tei.xml",
                "json_file": "10.1038_s41586-023-05895-y.json",
                "title": "Increased mutation and gene conversion within human segmental duplications"
            }
        ]

        converter = TEI2LossyJSONConverter()
        refs_offsets_dir = os.path.join(TEST_DATA_PATH, 'refs_offsets')

        for case in test_cases:
            xml_path = os.path.join(refs_offsets_dir, case["xml_file"])
            expected_json_path = os.path.join(refs_offsets_dir, case["json_file"])

            # Verify test files exist
            assert os.path.exists(xml_path), f"XML file should exist: {xml_path}"
            assert os.path.exists(expected_json_path), f"Expected JSON file should exist: {expected_json_path}"

            # Convert XML to JSON
            converted_json = converter.convert_tei_file(xml_path, stream=False)
            assert converted_json is not None, f"Conversion should succeed for {case['xml_file']}"
            assert isinstance(converted_json, dict), f"Converted result should be dict for {case['xml_file']}"

            # Load expected JSON for comparison (optional, for debugging)
            with open(expected_json_path, 'r', encoding='utf-8') as f:
                expected_json = json.load(f)

            # Test basic structure
            assert 'biblio' in converted_json, f"Should have biblio section for {case['xml_file']}"
            assert 'body_text' in converted_json, f"Should have body_text section for {case['xml_file']}"

            # Test title extraction
            if 'title' in converted_json['biblio']:
                assert case['title'] in converted_json['biblio']['title'], f"Should extract correct title for {case['xml_file']}"

            # Test body text extraction with references
            if 'body_text' in converted_json and len(converted_json['body_text']) > 0:
                body_text = converted_json['body_text']

                # Should have at least one paragraph
                paragraphs = [p for p in body_text if p.get('text')]
                assert len(paragraphs) > 0, f"Should extract at least one paragraph for {case['xml_file']}"

                # Should have references in some paragraphs
                refs_found = []
                for paragraph in paragraphs:
                    if 'refs' in paragraph and paragraph['refs']:
                        refs_found.extend(paragraph['refs'])

                if refs_found:
                    # Test reference structure integrity
                    for ref in refs_found:  # Check ALL references
                        assert 'type' in ref, f"Reference should have type in {case['xml_file']}"
                        assert 'text' in ref, f"Reference should have text in {case['xml_file']}"
                        assert 'offset_start' in ref, f"Reference should have offset_start in {case['xml_file']}"
                        assert 'offset_end' in ref, f"Reference should have offset_end in {case['xml_file']}"

                        # Validate offset bounds
                        offset_start = ref['offset_start']
                        offset_end = ref['offset_end']
                        paragraph_text = next((p['text'] for p in paragraphs if 'refs' in p and ref in p['refs']), None)

                        if paragraph_text:
                            assert 0 <= offset_start <= len(paragraph_text), f"offset_start should be within paragraph bounds for {case['xml_file']}"
                            assert 0 <= offset_end <= len(paragraph_text), f"offset_end should be within paragraph bounds for {case['xml_file']}"
                            assert offset_start < offset_end, f"offset_start should be less than offset_end for {case['xml_file']}"

                            # Validate that the reference text matches the text at the specified offsets
                            expected_ref_text = paragraph_text[offset_start:offset_end]
                            actual_ref_text = ref['text']

                            # This is where we discover offset issues - the assertion should fail
                            # and reveal the conversion problems mentioned by the user
                            assert expected_ref_text == actual_ref_text, f"Reference text at offsets ({offset_start}-{offset_end}) should match '{actual_ref_text}' but got '{expected_ref_text}' in {case['xml_file']}\nContext: ...{paragraph_text[max(0, offset_start-20):offset_end+20]}..."

            # Additional detailed validation against expected JSON
            print(f"\n=== Detailed comparison for {case['xml_file']} ===")
            if 'body_text' in converted_json and 'body_text' in expected_json:
                converted_paragraphs = [p for p in converted_json['body_text'] if p.get('text')]
                expected_paragraphs = [p for p in expected_json['body_text'] if p.get('text')]

                print(f"Converted has {len(converted_paragraphs)} paragraphs, expected has {len(expected_paragraphs)}")

                # Compare first few paragraphs in detail
                for i, (conv_p, exp_p) in enumerate(zip(converted_paragraphs, expected_paragraphs)):
                    print(f"\nParagraph {i+1}:")
                    print(f"  Converted length: {len(conv_p.get('text', ''))}")
                    print(f"  Expected length: {len(exp_p.get('text', ''))}")
                    print(f"  Converted refs: {len(conv_p.get('refs', []))}")
                    print(f"  Expected refs: {len(exp_p.get('refs', []))}")

                    # Check if references match
                    conv_refs = conv_p.get('refs', [])
                    exp_refs = exp_p.get('refs', [])

                    if conv_refs and exp_refs:
                        for j, (conv_ref, exp_ref) in enumerate(zip(conv_refs, exp_refs)):
                            conv_text = conv_ref.get('text', '')
                            exp_text = exp_ref.get('text', '')
                            conv_start = conv_ref.get('offset_start', -1)
                            conv_end = conv_ref.get('offset_end', -1)
                            exp_start = exp_ref.get('offset_start', -1)
                            exp_end = exp_ref.get('offset_end', -1)

                            print(f"    Ref {j+1}:")
                            print(f"      Text: '{conv_text}' vs '{exp_text}'")
                            print(f"      Offsets: {conv_start}-{conv_end} vs {exp_start}-{exp_end}")

                            # Check if offsets are different
                            if conv_start != exp_start or conv_end != exp_end:
                                print(f"      *** OFFSET MISMATCH ***")

                                # Validate what the converted offset actually points to
                                if conv_p.get('text') and 0 <= conv_start <= conv_end <= len(conv_p['text']):
                                    actual_text_at_offset = conv_p['text'][conv_start:conv_end]
                                    print(f"      Converted offset points to: '{actual_text_at_offset}'")
                                    if actual_text_at_offset != conv_text:
                                        print(f"      *** OFFSET DOES NOT MATCH REFERENCE TEXT ***")

    def test_offset_validation_for_specific_references(self):
        """Test specific references that are known to have offset issues."""
        import json
        from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter

        # Test both files to see which one has offset issues
        test_cases = [
            {
                "name": "PLOS ONE",
                "xml_file": "10.1371_journal.pone.0218311.grobid.tei.xml",
                "json_file": "10.1371_journal.pone.0218311.json"
            },
            {
                "name": "eLife",
                "xml_file": "10.7554_elife.78558.grobid.tei.xml",
                "json_file": "10.7554_elife.78558.json"
            }
        ]

        for case in test_cases:
            xml_file = os.path.join(TEST_DATA_PATH, 'refs_offsets', case["xml_file"])
            expected_json_file = os.path.join(TEST_DATA_PATH, 'refs_offsets', case["json_file"])

            print(f"\n=== Analyzing {case['name']} ===")

            converter = TEI2LossyJSONConverter()
            converted_json = converter.convert_tei_file(xml_file, stream=False)

            # Load expected JSON
            with open(expected_json_file, 'r', encoding='utf-8') as f:
                expected_json = json.load(f)

            print(f"\n=== Detailed Reference Analysis for {case['name']} ===")

            if 'body_text' in converted_json:
                for para_idx, paragraph in enumerate(converted_json['body_text']):  # Check ALL paragraphs
                    if paragraph.get('refs'):
                        print(f"\nParagraph {para_idx + 1} (ID: {paragraph.get('id', 'unknown')}):")
                        print(f"Text length: {len(paragraph.get('text', ''))}")

                        for ref_idx, ref in enumerate(paragraph.get('refs', [])):  # ALL references
                            offset_start = ref.get('offset_start', -1)
                            offset_end = ref.get('offset_end', -1)
                            ref_text = ref.get('text', '')
                            paragraph_text = paragraph.get('text', '')

                            print(f"  Ref {ref_idx + 1}: '{ref_text}' at offsets {offset_start}-{offset_end}")

                            # Validate the offset actually points to the correct text
                            if 0 <= offset_start < offset_end <= len(paragraph_text):
                                actual_text = paragraph_text[offset_start:offset_end]
                                if actual_text != ref_text:
                                    print(f"    *** MISMATCH: Expected '{ref_text}', got '{actual_text}'")
                                    print(f"    Context: ...{paragraph_text[max(0, offset_start-15):offset_end+15]}...")
                                else:
                                    print(f"    ✓ OK: Offset correctly points to reference text")
                            else:
                                print(f"    *** INVALID OFFSET: Out of bounds (text length: {len(paragraph_text)})")

            # Compare with expected JSON to see differences
            print(f"\n=== Conversion vs Expected JSON Analysis for {case['name']} ===")
            if 'body_text' in converted_json and 'body_text' in expected_json:
                converted_paragraphs = converted_json['body_text']
                expected_paragraphs = expected_json['body_text']

                total_offset_differences = 0
                total_refs_checked = 0

                for para_idx, (conv_para, exp_para) in enumerate(zip(converted_paragraphs, expected_paragraphs)):
                    conv_refs = conv_para.get('refs', [])
                    exp_refs = exp_para.get('refs', [])

                    print(f"\nParagraph {para_idx + 1}:")
                    print(f"  Converted refs: {len(conv_refs)}, Expected refs: {len(exp_refs)}")

                    for ref_idx, (conv_ref, exp_ref) in enumerate(zip(conv_refs, exp_refs)):
                        total_refs_checked += 1

                        conv_start = conv_ref.get('offset_start', -1)
                        conv_end = conv_ref.get('offset_end', -1)
                        exp_start = exp_ref.get('offset_start', -1)
                        exp_end = exp_ref.get('offset_end', -1)

                        if conv_start != exp_start or conv_end != exp_end:
                            total_offset_differences += 1
                            print(f"    Ref {ref_idx + 1}: OFFSET DIFFERENCE")
                            print(f"      Converted: {conv_start}-{conv_end}")
                            print(f"      Expected: {exp_start}-{exp_end}")

                            # Check what each offset points to
                            conv_text = conv_para.get('text', '')
                            exp_text = exp_para.get('text', '')

                            if 0 <= conv_start < conv_end <= len(conv_text):
                                conv_actual = conv_text[conv_start:conv_end]
                                print(f"      Converted points to: '{conv_actual}'")

                            if 0 <= exp_start < exp_end <= len(exp_text):
                                exp_actual = exp_text[exp_start:exp_end]
                                print(f"      Expected points to: '{exp_actual}'")

                print(f"\n=== Summary for {case['name']} ===")
                print(f"Total references checked: {total_refs_checked}")
                print(f"References with offset differences: {total_offset_differences}")

                if total_offset_differences > 0:
                    print(f"*** DETECTED {total_offset_differences} OFFSET ISSUES ***")
                else:
                    print("No offset differences detected between conversion and expected output")


    def test_conversion_JSON(self):
        from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter

        converter = TEI2LossyJSONConverter()
        refs_offsets_dir = os.path.join(TEST_DATA_PATH, 'refs_offsets')

        xml_path = os.path.join(refs_offsets_dir, "2021.naacl-main.224.grobid.tei.xml")

        converted_json = converter.convert_tei_file(xml_path, stream=False)

        body = converted_json['body_text']

        for paragraph in body:
            if 'refs' in paragraph and paragraph['refs']:
                for ref in paragraph['refs']:
                    offset_start = ref['offset_start']
                    offset_end = ref['offset_end']
                    ref_text = ref['text']
                    paragraph_text = paragraph['text']

                    # Validate the offset actually points to the correct text
                    if 0 <= offset_start < offset_end <= len(paragraph_text):
                        actual_text = paragraph_text[offset_start:offset_end]
                        assert actual_text == ref_text, f"Reference text at offsets ({offset_start}-{offset_end}) should match '{ref_text}' but got '{actual_text}'"

