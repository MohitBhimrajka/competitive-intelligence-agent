import os
import io
import re
import tempfile
import logging
import markdown
import base64
from datetime import datetime
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS # Import CSS for potential future use

logger = logging.getLogger(__name__)

# --- Default Agent Description ---
DEFAULT_AGENT_DESCRIPTION = "Leveraging advanced AI for automated competitor monitoring and analysis."
# ---

class PDFService:
    def __init__(self):
        """Initialize the PDF service with Jinja2 template environment."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_dir = os.path.join(base_dir, 'templates')

        if not os.path.exists(template_dir):
            os.makedirs(template_dir)

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        logger.info(f"PDF Service initialized with template directory: {template_dir}")

    def _extract_table_of_contents(self, markdown_text: str) -> List[dict]:
        """Extract headers from markdown to create a table of contents."""
        toc = []
        # Regex to match markdown headers (#, ##, etc.) and capture level and text
        header_regex = re.compile(r'^(#{1,6})\s+(.*)')
        # Simplified ID generation: lower case, replace space with -, remove some chars
        # Important: Needs to match the ID generation in _preprocess_markdown
        id_cleaner = re.compile(r'[^\w\s-]') # Keep word chars, whitespace, hyphen
        space_replacer = re.compile(r'\s+')

        for line in markdown_text.splitlines():
            match = header_regex.match(line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                # Generate a cleaner ID
                temp_id = text.lower()
                temp_id = id_cleaner.sub('', temp_id) # Remove invalid chars
                header_id = space_replacer.sub('-', temp_id).strip('-') # Replace spaces, trim ends

                # Avoid empty IDs or duplicates if possible (simple check)
                if header_id and not any(entry['id'] == header_id for entry in toc):
                    toc.append({'level': level, 'text': text, 'id': header_id})
                elif header_id:
                     # Handle duplicate ID - append a number? For now, log and potentially skip or append '-dup'
                     logger.warning(f"Duplicate or empty header ID generated: '{header_id}' for text: '{text}'. TOC linking might be affected.")
                     # toc.append({'level': level, 'text': text, 'id': f"{header_id}-{len(toc)}"}) # Option: append index

        return toc

    def _generate_toc_html(self, toc_entries: List[dict]) -> str:
        """Generate HTML for table of contents."""
        toc_html = ""
        min_level = min((entry['level'] for entry in toc_entries), default=1)

        for entry in toc_entries:
            # Adjust indentation based on level relative to the minimum level found
            indent = (entry['level'] - min_level) * 20 # Indent relative to shallowest header
            indent = max(0, indent) # Ensure non-negative indent

            # Page numbers will be filled by WeasyPrint
            toc_html += f'''
            <div class="toc-entry" style="margin-left: {indent}px">
                <a href="#{entry['id']}">{entry['text']}</a>
                <div class="toc-dots"></div>
                <span class="toc-page"></span>
            </div>
            '''
        return toc_html

    def _preprocess_markdown(self, markdown_text: str) -> str:
        """Add IDs to headers for TOC linking. Must match ID generation in _extract_table_of_contents."""
        processed_lines = []
        header_regex = re.compile(r'^(#{1,6})\s+(.*)')
        id_cleaner = re.compile(r'[^\w\s-]')
        space_replacer = re.compile(r'\s+')
        seen_ids = set() # Track generated IDs to handle duplicates

        for line in markdown_text.splitlines():
            match = header_regex.match(line)
            if match:
                level_hashes = match.group(1)
                text = match.group(2).strip()
                # Generate ID exactly as in _extract_table_of_contents
                temp_id = text.lower()
                temp_id = id_cleaner.sub('', temp_id)
                header_id = space_replacer.sub('-', temp_id).strip('-')

                # Handle duplicate IDs by appending a counter
                original_id = header_id
                count = 1
                while header_id in seen_ids:
                    header_id = f"{original_id}-{count}"
                    count += 1
                if header_id: # Only add ID if it's not empty
                    seen_ids.add(header_id)
                    # Inject the anchor tag before the text
                    processed_lines.append(f'{level_hashes} <a id="{header_id}"></a>{text}')
                else:
                    logger.warning(f"Skipping empty ID for header: '{text}'")
                    processed_lines.append(line) # Add original line if ID is empty

            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)


    # Renamed title -> report_title for clarity
    def _render_html_report_buffer(self, markdown_text: str, report_title: str, report_subtitle: str, agent_description: str) -> io.BytesIO:
        """Convert markdown to HTML and return it in a buffer."""
        try:
            # Preprocess markdown to add IDs to headers
            processed_markdown = self._preprocess_markdown(markdown_text)

            # Extract TOC entries *after* preprocessing IDs if needed for consistency (though extract uses raw text)
            toc_entries = self._extract_table_of_contents(markdown_text) # Use original text for TOC text
            toc_html = self._generate_toc_html(toc_entries)

            # Convert markdown to HTML
            html_content = markdown.markdown(
                processed_markdown,
                extensions=['extra', 'tables', 'fenced_code', 'sane_lists', 'nl2br'] # Common extensions
                # Note: 'toc' extension here generates its own TOC, we are creating ours manually
            )

            # Render the HTML template
            template = self.env.get_template('report_template.html')
            html_with_style = template.render(
                report_title=report_title,         # Use the new variable name
                report_subtitle=report_subtitle, # Pass new subtitle
                date=datetime.now().strftime("%B %d, %Y"),
                toc_content=toc_html,
                content=html_content,
                agent_description=agent_description # Pass new description
            )

            # Save HTML to a buffer
            html_buffer = io.BytesIO()
            html_buffer.write(html_with_style.encode('utf-8'))
            html_buffer.seek(0)

            logger.info(f"HTML content successfully generated for: {report_title}")
            return html_buffer

        except Exception as e:
            logger.error(f"Error generating HTML: {e}", exc_info=True) # Added exc_info
            raise

    def generate_pdf_from_html_buffer(self, html_buffer: io.BytesIO) -> io.BytesIO:
        """Convert an HTML buffer to a PDF buffer using WeasyPrint."""
        try:
            pdf_buffer = io.BytesIO()
            # Pass the HTML object to WeasyPrint
            html = HTML(file_obj=html_buffer)
            html.write_pdf(pdf_buffer) # No need for stylesheets argument unless adding separate CSS files
            pdf_buffer.seek(0)

            logger.info("PDF successfully generated from HTML buffer")
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error generating PDF from HTML: {e}", exc_info=True) # Added exc_info
            raise

    # Kept title for backward compatibility if called directly, but prefer report_title
    def markdown_to_pdf(self, markdown_text: str, title: str) -> io.BytesIO:
        """Legacy method - DEPRECATED - Use generate_single_report_pdf instead."""
        logger.warning("markdown_to_pdf is deprecated. Use generate_single_report_pdf.")
        # Use default subtitle/description for legacy calls
        html_buffer = self._render_html_report_buffer(
            markdown_text,
            report_title=title,
            report_subtitle="Deep Dive Research", # Default subtitle
            agent_description=DEFAULT_AGENT_DESCRIPTION
        )
        return self.generate_pdf_from_html_buffer(html_buffer)

    # Renamed title -> report_title
    def generate_single_report_pdf(self, markdown_text: str, report_title: str) -> io.BytesIO:
        """Generate a PDF report from markdown text."""
        # Provide specific subtitle for single reports
        html_buffer = self._render_html_report_buffer(
            markdown_text,
            report_title=report_title,
            report_subtitle="Deep Dive Research", # Specific subtitle
            agent_description=DEFAULT_AGENT_DESCRIPTION
            )
        return self.generate_pdf_from_html_buffer(html_buffer)

    def combine_markdown_files(self, markdown_files: List[str], competitor_names: List[str]) -> str:
        """Combine multiple markdown files into a single markdown document, ensuring headers."""
        combined_markdown = ""

        for i, (md_file, competitor_name) in enumerate(zip(markdown_files, competitor_names)):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip() # Read and strip whitespace

                # Add a section separator (page break in CSS) before the second competitor onwards
                if i > 0:
                    combined_markdown += "\n\n<div class='competitor-section' style='page-break-before: always;'></div>\n\n" # Add style for page break

                # Add competitor name as a top-level header if content doesn't already start with one
                # Check if content starts with any level of markdown header (#, ##, etc.)
                if not content.startswith("#"):
                     combined_markdown += f"# {competitor_name}\n\n" # Add H1 if missing

                combined_markdown += content + "\n\n" # Add content and extra newline

            except FileNotFoundError:
                logger.error(f"Markdown file not found: {md_file}. Skipping.")
            except Exception as e:
                logger.error(f"Error processing markdown file {md_file}: {e}")

        return combined_markdown.strip() # Return combined text, stripped


    # Renamed title -> report_title
    def generate_combined_report_pdf(self, markdown_files: List[str], competitor_names: List[str], title: str) -> io.BytesIO:
        """Generate a combined PDF report from multiple markdown files."""
        combined_markdown = self.combine_markdown_files(markdown_files, competitor_names)
        # Provide specific subtitle for combined reports
        html_buffer = self._render_html_report_buffer(
            combined_markdown,
            report_title=title,
            report_subtitle="Comparative Analysis of Key Competitors", # Specific subtitle
            agent_description=DEFAULT_AGENT_DESCRIPTION
            )
        return self.generate_pdf_from_html_buffer(html_buffer)

# Create a singleton instance
pdf_service = PDFService()