"""
Convert TEI XML format to Markdown format

This module provides functionality to convert GROBID TEI XML output to a clean
Markdown format with the following sections:
- Title
- Authors
- Affiliations  
- Publication date
- Fulltext
- Annex
- References
"""
import os
import uuid
from pathlib import Path
from typing import List, Dict, Union, Optional, BinaryIO
from bs4 import BeautifulSoup, NavigableString, Tag
import logging
import dateparser

# Configure module-level logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Basic configuration if not already configured by the application
    logging.basicConfig(level=logging.INFO)


class TEI2MarkdownConverter:
    """Converter that converts TEI XML to Markdown format."""

    def __init__(self):
        pass

    def convert_tei_file(self, tei_file: Union[Path, BinaryIO]) -> Optional[str]:
        """Convert a TEI file to Markdown format.
        
        Args:
            tei_file: Path to TEI file or file-like object
            
        Returns:
            Markdown content as string, or None if conversion fails
        """
        try:
            # Load with BeautifulSoup
            if isinstance(tei_file, (str, Path)):
                content = open(tei_file, 'r', encoding='utf-8').read()
            else:
                content = tei_file.read()
                
            soup = BeautifulSoup(content, 'xml')

            if soup.TEI is None:
                logger.warning("The TEI file is not well-formed or empty. Skipping the file.")
                return None

            markdown_sections = []
            
            # Extract title
            title = self._extract_title(soup)
            if title:
                markdown_sections.append(f"# {title}\n")

            # Extract authors
            authors = self._extract_authors(soup)
            if authors:
                for author in authors:
                    markdown_sections.append(f"{author}\n")
                markdown_sections.append("\n")

            # Extract affiliations
            affiliations = self._extract_affiliations(soup)
            if affiliations:
                affiliations_as_text = ", ".join(affiliations)
                markdown_sections.append(f"{affiliations_as_text}\n\n")

            # Extract publication date
            pub_date = self._extract_publication_date(soup)
            if pub_date:
                markdown_sections.append(f"Publishd on {pub_date}\n\n")

            # Extract fulltext
            fulltext = self._extract_fulltext(soup)
            if fulltext:
                markdown_sections.append(fulltext)
                markdown_sections.append("\n")

            # Extract annex (acknowledgements, competing interests, etc.)
            annex = self._extract_annex(soup)
            if annex:
                markdown_sections.append(annex)
                markdown_sections.append("\n")

            # Extract references
            references = self._extract_references(soup)
            if references:
                markdown_sections.append("## References\n")
                markdown_sections.append(references)
                markdown_sections.append("\n")
            
            return "".join(markdown_sections)
            
        except Exception as e:
            logger.error(f"Error converting TEI to Markdown: {str(e)}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract document title from TEI."""
        title_node = soup.find("title", attrs={"type": "main", "level": "a"})
        if title_node:
            return title_node.get_text().strip()
        return None

    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract authors from TEI document header (excluding references)."""
        authors = []

        # Only look in teiHeader to avoid picking up authors from references
        tei_header = soup.find("teiHeader")
        if not tei_header:
            return authors

        for author in tei_header.find_all("author"):
            forename = author.find('forename')
            surname = author.find('surname')

            if forename and surname:
                author_name = f"{forename.get_text().strip()} {surname.get_text().strip()}"
            elif surname:
                author_name = surname.get_text().strip()
            elif forename:
                author_name = forename.get_text().strip()
            else:
                continue

            if author_name.strip():
                authors.append(author_name.strip())

        return authors

    def _extract_affiliations(self, soup: BeautifulSoup) -> List[str]:
        """Extract affiliations from TEI document header (excluding references)."""
        affiliations = []

        # Only look in teiHeader to avoid picking up affiliations from references
        tei_header = soup.find("teiHeader")
        if not tei_header:
            return affiliations

        for affiliation in tei_header.find_all("affiliation"):
            # Get the full affiliation text
            affiliation_text = affiliation.get_text().strip()
            if affiliation_text:
                affiliations.append(affiliation_text)

        return affiliations

    def _extract_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date from TEI."""
        pub_date = soup.find("date", attrs={"type": "published"})
        if pub_date:
            iso_date = pub_date.attrs.get("when")
            if iso_date:
                try:
                    parsed_date = dateparser.parse(iso_date)
                    if parsed_date:
                        return parsed_date.strftime("%B %d, %Y")
                except Exception:
                    pass
                return iso_date
        return None

    def _extract_fulltext(self, soup: BeautifulSoup) -> str:
        """Extract main body text from TEI."""
        fulltext_sections = []
        
        # Find body element
        body = soup.find("body")
        if not body:
            return ""
        
        # Process each div in the body
        for div in body.find_all("div"):
            # Get section heading
            head = div.find("head")
            if head:
                section_title = head.get_text().strip()
                fulltext_sections.append(f"### {section_title}\n")

            # Get paragraphs
            paragraphs = div.find_all("p")
            for p in paragraphs:
                paragraph_text = self._process_paragraph(p)
                if paragraph_text.strip():
                    fulltext_sections.append(f"{paragraph_text}\n\n")
        
        return "".join(fulltext_sections)

    def _extract_annex(self, soup: BeautifulSoup) -> str:
        """Extract annex content (everything in <back> except references) from TEI."""
        annex_sections = []

        # Find back element
        back = soup.find("back")
        if not back:
            return ""

        # Remove references from back so they don't get included in annex
        # References are handled separately by _extract_references
        back_copy = back
        for list_bibl in back_copy.find_all("listBibl"):
            list_bibl.decompose()  # Remove references element

        # Get all content from back (not just divs) - stream everything
        for child in back_copy.children:
            if hasattr(child, 'name') and child.name:
                if child.name == "div":
                    # Process div content without section headers
                    paragraphs = child.find_all("p")
                    for p in paragraphs:
                        paragraph_text = self._process_paragraph(p)
                        if paragraph_text.strip():
                            annex_sections.append(f"{paragraph_text}\n\n")
                elif child.name == "p":
                    # Direct paragraphs in back
                    paragraph_text = self._process_paragraph(child)
                    if paragraph_text.strip():
                        annex_sections.append(f"{paragraph_text}\n\n")
                # Add other elements as needed (e.g., notes, etc.)
                elif child.name not in ["listBibl"]:  # Skip references, already removed
                    # Get text content from other elements
                    text_content = child.get_text().strip()
                    if text_content:
                        annex_sections.append(f"{text_content}\n\n")

        return "".join(annex_sections)

    def _extract_references(self, soup: BeautifulSoup) -> str:
        """Extract bibliographic references from TEI."""
        references = []
        
        # Find listBibl element
        list_bibl = soup.find("listBibl")
        if not list_bibl:
            return ""
        
        # Process each biblStruct
        for i, bibl_struct in enumerate(list_bibl.find_all("biblStruct"), 1):
            ref_text = self._format_reference(bibl_struct, i)
            if ref_text:
                references.append(ref_text)
        
        return "\n".join(references)

    def _process_paragraph(self, p_element: Tag) -> str:
        """Process a paragraph element and convert to markdown."""
        text_parts = []
        
        for element in p_element.children:
            if isinstance(element, NavigableString):
                text_parts.append(str(element))
            elif element.name == "ref":
                # Handle references - keep the text but don't add special formatting
                ref_text = element.get_text()
                text_parts.append(ref_text)
            elif element.name == "figure":
                # Handle figures
                fig_desc = element.find("figDesc")
                if fig_desc:
                    text_parts.append(f"\n*Figure: {fig_desc.get_text().strip()}*\n")
            elif element.name == "table":
                # Handle tables - convert to simple markdown
                table_md = self._table_to_markdown(element)
                if table_md:
                    text_parts.append(f"\n{table_md}\n")
            else:
                # For other elements, just get the text
                text_parts.append(element.get_text())
        
        return "".join(text_parts).strip()

    def _table_to_markdown(self, table_element: Tag) -> str:
        """Convert a table element to simple markdown."""
        markdown_lines = []
        
        # Process table rows
        for row in table_element.find_all("row"):
            cells = []
            for cell in row.find_all("cell"):
                cell_text = cell.get_text().strip()
                cells.append(cell_text)
            
            if cells:
                markdown_lines.append("| " + " | ".join(cells) + " |")
        
        return "\n".join(markdown_lines) if markdown_lines else ""

    def _format_reference(self, bibl_struct: Tag, ref_num: int) -> str:
        """Format a bibliographic reference."""
        ref_parts = []
        
        # Get title
        title = bibl_struct.find("title", level="a")
        if title:
            ref_parts.append(f"**[{ref_num}]** {title.get_text().strip()}")
        
        # Get authors
        authors = []
        for author in bibl_struct.find_all("author"):
            forename = author.find('forename')
            surname = author.find('surname')
            
            if forename and surname:
                author_name = f"{forename.get_text().strip()} {surname.get_text().strip()}"
            elif surname:
                author_name = surname.get_text().strip()
            elif forename:
                author_name = forename.get_text().strip()
            else:
                continue
                
            if author_name.strip():
                authors.append(author_name.strip())
        
        if authors:
            if len(authors) == 1:
                ref_parts.append(f"*{authors[0]}*")
            elif len(authors) == 2:
                ref_parts.append(f"*{authors[0]} and {authors[1]}*")
            else:
                ref_parts.append(f"*{authors[0]} et al.*")
        
        # Get journal/venue
        journal = bibl_struct.find("title", level="j")
        if journal:
            ref_parts.append(f"*{journal.get_text().strip()}*")
        
        # Get date
        date = bibl_struct.find("date")
        if date:
            date_text = date.get_text().strip()
            if date_text:
                ref_parts.append(f"({date_text})")
        
        return ". ".join(ref_parts) + "."


# Backwards compatible top-level function
def convert_tei_file_to_markdown(tei_file: Union[Path, BinaryIO]) -> Optional[str]:
    """Convert a TEI file to Markdown format.
    
    Args:
        tei_file: Path to TEI file or file-like object
        
    Returns:
        Markdown content as string, or None if conversion fails
    """
    converter = TEI2MarkdownConverter()
    return converter.convert_tei_file(tei_file)
