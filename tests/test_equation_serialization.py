"""
Unit tests for equation/formula serialization in TEI to JSON and Markdown conversions.
"""
import os
from grobid_client.format.TEI2Markdown import TEI2MarkdownConverter
from grobid_client.format.TEI2LossyJSON import TEI2LossyJSONConverter
from tests.resources import TEST_DATA_PATH


class TestEquationSerialization:
    """Test cases for equation/formula serialization in conversions."""

    def test_formulas_in_markdown_output(self):
        """Test that formulas are included in Markdown output."""
        # Use test file known to contain formulas
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')
        assert os.path.exists(tei_file), f"Test file should exist: {tei_file}"

        # Convert to Markdown
        converter = TEI2MarkdownConverter()
        markdown_output = converter.convert_tei_file(tei_file)

        # Verify conversion succeeded
        assert markdown_output is not None, "Markdown conversion should not return None"
        assert isinstance(markdown_output, str), "Markdown should be a string"
        assert len(markdown_output) > 0, "Markdown should have content"

        # Check that formulas are present (they should be in code blocks)
        assert '```' in markdown_output, "Formulas should be formatted as code blocks"

        # Check for specific formula content from the test file
        # The test file has formulas with "Fext" and equation numbers
        assert 'Fext' in markdown_output, "Formula variables should appear in output"
        assert 'ð1Þ' in markdown_output or '(1)' in markdown_output, "Equation labels should appear"

        # Count code blocks (each formula uses ``` for opening and closing)
        code_block_count = markdown_output.count('```') // 2
        assert code_block_count >= 2, "Should have at least 2 formulas in test file"

    def test_formulas_in_json_output(self):
        """Test that formulas are included in JSON output."""
        # Use test file known to contain formulas
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')
        assert os.path.exists(tei_file), f"Test file should exist: {tei_file}"

        # Convert to JSON
        converter = TEI2LossyJSONConverter()
        json_output = converter.convert_tei_file(tei_file, stream=False)

        # Verify conversion succeeded
        assert json_output is not None, "JSON conversion should not return None"
        assert isinstance(json_output, dict), "JSON should be a dictionary"

        # Check body_text contains formulas
        body_text = json_output.get('body_text', [])
        assert len(body_text) > 0, "Should have body_text entries"

        # Find formula entries
        formulas = [entry for entry in body_text if entry.get('type') == 'formula']
        assert len(formulas) >= 2, "Should have at least 2 formulas"

        # Verify formula structure
        for formula in formulas:
            assert 'id' in formula, "Formula should have ID"
            assert 'type' in formula, "Formula should have type"
            assert formula['type'] == 'formula', "Type should be 'formula'"
            assert 'text' in formula, "Formula should have text content"
            assert len(formula['text']) > 0, "Formula text should not be empty"

        # Check specific formulas from the test file
        formula_texts = [f.get('text', '') for f in formulas]
        assert any('Fext' in text for text in formula_texts), "Should have formula with 'Fext'"

        # Check labels
        formula_labels = [f.get('label', '') for f in formulas]
        assert any(label for label in formula_labels), "At least one formula should have a label"

    def test_formula_ordering_in_json(self):
        """Test that formulas appear in correct order relative to paragraphs."""
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')
        assert os.path.exists(tei_file), f"Test file should exist: {tei_file}"

        # Convert to JSON
        converter = TEI2LossyJSONConverter()
        json_output = converter.convert_tei_file(tei_file, stream=False)

        body_text = json_output.get('body_text', [])

        # Find entries in "Data analysis" section
        data_analysis_entries = [
            entry for entry in body_text
            if entry.get('head_section') == 'Data analysis'
        ]

        assert len(data_analysis_entries) > 0, "Should have Data analysis section"

        # The first entry should be a paragraph about "Percentage of fingers extensions"
        first_entry = data_analysis_entries[0]
        assert first_entry.get('type') != 'formula', "First entry should be a paragraph"
        assert 'Percentage' in first_entry.get('text', ''), "First paragraph should mention 'Percentage'"

        # A formula should come before the paragraph starting with "Where Fext"
        found_formula_before_where = False
        for i, entry in enumerate(data_analysis_entries[:-1]):
            if entry.get('type') == 'formula':
                next_entry = data_analysis_entries[i + 1]
                if 'Where' in next_entry.get('text', ''):
                    found_formula_before_where = True
                    break

        assert found_formula_before_where, "Formula should appear before explanatory paragraph"

    def test_formula_with_label_structure(self):
        """Test that formulas with labels are properly structured."""
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')

        # Convert to JSON
        converter = TEI2LossyJSONConverter()
        json_output = converter.convert_tei_file(tei_file, stream=False)

        body_text = json_output.get('body_text', [])
        formulas = [entry for entry in body_text if entry.get('type') == 'formula']

        # Find formula with label
        formulas_with_labels = [f for f in formulas if f.get('label')]
        assert len(formulas_with_labels) > 0, "Should have formulas with labels"

        # Check that formula text doesn't include the label
        for formula in formulas_with_labels:
            label = formula.get('label', '')
            text = formula.get('text', '')
            # The label should be separate from the formula text
            assert label, "Label should not be empty"
            # Label like "(1)" or "ð1Þ" should not appear at the end of text
            assert not text.endswith(label), "Formula text should not end with label"

    def test_formula_coordinates(self):
        """Test that formula coordinates are preserved if available."""
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')

        # Convert to JSON
        converter = TEI2LossyJSONConverter()
        json_output = converter.convert_tei_file(tei_file, stream=False)

        body_text = json_output.get('body_text', [])
        formulas = [entry for entry in body_text if entry.get('type') == 'formula']

        # Check if formulas have coords
        for formula in formulas:
            assert 'coords' in formula, "Formula should have coords field"
            # coords can be empty list if not available in source
            assert isinstance(formula['coords'], list), "Coords should be a list"

    def test_formula_xml_id_preserved(self):
        """Test that xml:id attribute is preserved for formulas."""
        tei_file = os.path.join(TEST_DATA_PATH, '0046d83a-edd6-4631-b57c-755cdcce8b7f.tei.xml')

        # Convert to JSON
        converter = TEI2LossyJSONConverter()
        json_output = converter.convert_tei_file(tei_file, stream=False)

        body_text = json_output.get('body_text', [])
        formulas = [entry for entry in body_text if entry.get('type') == 'formula']

        # At least some formulas should have xml_id
        formulas_with_xml_id = [f for f in formulas if f.get('xml_id')]
        assert len(formulas_with_xml_id) > 0, "Some formulas should have xml_id"

        # Check format of xml_id
        for formula in formulas_with_xml_id:
            xml_id = formula.get('xml_id')
            assert xml_id.startswith('formula_'), f"xml_id should start with 'formula_': {xml_id}"

    def test_formulas_in_other_test_files(self):
        """Test formula serialization in other test files."""
        test_files = [
            '10.1371_journal.pone.0218311.grobid.tei.xml',
            '10.1038_s41586-023-05895-y.grobid.tei.xml'
        ]

        refs_offsets_dir = os.path.join(TEST_DATA_PATH, 'refs_offsets')

        for filename in test_files:
            filepath = os.path.join(refs_offsets_dir, filename)
            if not os.path.exists(filepath):
                continue

            print(f"\nTesting {filename}")

            # Test JSON conversion
            converter = TEI2LossyJSONConverter()
            json_output = converter.convert_tei_file(filepath, stream=False)

            if json_output:
                body_text = json_output.get('body_text', [])
                formulas = [entry for entry in body_text if entry.get('type') == 'formula']

                # If file has formulas, verify they're properly structured
                if len(formulas) > 0:
                    print(f"  Found {len(formulas)} formulas")
                    for formula in formulas:
                        assert 'text' in formula, f"Formula in {filename} should have text"
                        assert len(formula['text']) > 0, f"Formula text in {filename} should not be empty"

            # Test Markdown conversion
            md_converter = TEI2MarkdownConverter()
            md_output = md_converter.convert_tei_file(filepath)

            if md_output and len(formulas) > 0:
                # If JSON found formulas, Markdown should include them either as:
                # - code blocks (```) for formulas with labels
                # - inline code (`) for formulas without labels
                # So we just check for backticks in general
                assert '`' in md_output, f"Markdown for {filename} should contain formula code formatting"

    def test_empty_formula_handling(self):
        """Test that empty or malformed formulas don't break conversion."""
        # Create a minimal TEI with an empty formula
        import tempfile
        tei_content = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Test Document</title>
            </titleStmt>
        </fileDesc>
    </teiHeader>
    <text>
        <body>
            <div>
                <head>Test Section</head>
                <p>Before formula.</p>
                <formula xml:id="formula_empty"></formula>
                <p>After formula.</p>
            </div>
        </body>
    </text>
</TEI>"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tei.xml', delete=False) as f:
            f.write(tei_content)
            temp_file = f.name

        try:
            # Test JSON conversion
            converter = TEI2LossyJSONConverter()
            json_output = converter.convert_tei_file(temp_file, stream=False)
            assert json_output is not None, "Should handle empty formula gracefully"

            # Test Markdown conversion
            md_converter = TEI2MarkdownConverter()
            md_output = md_converter.convert_tei_file(temp_file)
            assert md_output is not None, "Markdown should handle empty formula gracefully"

        finally:
            os.unlink(temp_file)
