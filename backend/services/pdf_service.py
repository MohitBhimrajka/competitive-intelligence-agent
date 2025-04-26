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
from weasyprint import HTML  # Import WeasyPrint

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        """Initialize the PDF service with Jinja2 template environment."""
        # Set up the Jinja2 environment
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_dir = os.path.join(base_dir, 'templates')
        
        # Create templates directory if it doesn't exist
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
        for line in markdown_text.split('\n'):
            # Match headers (# Header)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2).strip()
                # Create an ID from the header text (simplified)
                header_id = text.lower().replace(' ', '-').replace(':', '').replace(',', '')
                toc.append({
                    'level': level,
                    'text': text,
                    'id': header_id
                })
        
        return toc
    
    def _generate_toc_html(self, toc_entries: List[dict]) -> str:
        """Generate HTML for table of contents."""
        toc_html = ""
        
        for entry in toc_entries:
            # Apply indentation based on header level
            indent = (entry['level'] - 1) * 20
            
            toc_html += f'''
            <div class="toc-entry" style="margin-left: {indent}px">
                <a href="#{entry['id']}">{entry['text']}</a>
                <div class="toc-dots"></div>
                <span class="toc-page"></span>
            </div>
            '''
            
        return toc_html
    
    def _preprocess_markdown(self, markdown_text: str) -> str:
        """Add IDs to headers for TOC linking."""
        processed_lines = []
        
        for line in markdown_text.split('\n'):
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = header_match.group(1)
                text = header_match.group(2)
                header_id = text.lower().replace(' ', '-').replace(':', '').replace(',', '')
                processed_lines.append(f'{level} <a id="{header_id}"></a>{text}')
            else:
                processed_lines.append(line)
                
        return '\n'.join(processed_lines)
    
    def _save_to_temp_file(self, content: str, extension: str = '.md') -> str:
        """Save content to a temporary file and return the path."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
        temp_file.write(content.encode('utf-8'))
        temp_file.close()
        return temp_file.name
    
    def _render_html_report_buffer(self, markdown_text: str, title: str) -> io.BytesIO:
        """Convert markdown to HTML and return it in a buffer (formerly markdown_to_pdf)."""
        try:
            # Preprocess markdown to add IDs to headers
            processed_markdown = self._preprocess_markdown(markdown_text)
            
            # Extract TOC entries
            toc_entries = self._extract_table_of_contents(markdown_text)
            toc_html = self._generate_toc_html(toc_entries)
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                processed_markdown, 
                extensions=['extra', 'sane_lists', 'nl2br', 'toc', 'tables', 'fenced_code']
            )
            
            # Render the HTML template
            template = self.env.get_template('report_template.html')
            html_with_style = template.render(
                title=title,
                date=datetime.now().strftime("%B %d, %Y"),
                toc_content=toc_html,
                content=html_content
            )
            
            # Save HTML to a buffer
            html_buffer = io.BytesIO()
            html_buffer.write(html_with_style.encode('utf-8'))
            html_buffer.seek(0)
            
            logger.info(f"HTML content successfully generated for: {title}")
            return html_buffer
            
        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            raise
    
    def generate_pdf_from_html_buffer(self, html_buffer: io.BytesIO) -> io.BytesIO:
        """Convert an HTML buffer to a PDF buffer using WeasyPrint."""
        try:
            pdf_buffer = io.BytesIO()
            HTML(file_obj=html_buffer).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            logger.info("PDF successfully generated from HTML buffer")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF from HTML: {e}")
            raise
    
    def markdown_to_pdf(self, markdown_text: str, title: str) -> io.BytesIO:
        """Legacy method that now returns HTML - kept for backward compatibility."""
        return self._render_html_report_buffer(markdown_text, title)
    
    def generate_single_report_pdf(self, markdown_text: str, title: str) -> io.BytesIO:
        """Generate a PDF report from markdown text."""
        html_buffer = self._render_html_report_buffer(markdown_text, title)
        return self.generate_pdf_from_html_buffer(html_buffer)
    
    def combine_markdown_files(self, markdown_files: List[str], competitor_names: List[str]) -> str:
        """Combine multiple markdown files into a single markdown document."""
        combined_markdown = ""
        
        for i, (md_file, competitor_name) in enumerate(zip(markdown_files, competitor_names)):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Add a section separator for each competitor except the first one
            if i > 0:
                combined_markdown += f"\n\n<div class='competitor-section'></div>\n\n"
                
            # Add competitor name as a top-level header if not already present
            if not content.strip().startswith(f"# {competitor_name}"):
                combined_markdown += f"# {competitor_name}\n\n"
                
            combined_markdown += content
            
        return combined_markdown
    
    def generate_combined_report_pdf(self, markdown_files: List[str], competitor_names: List[str], title: str) -> io.BytesIO:
        """Generate a combined PDF report from multiple markdown files."""
        combined_markdown = self.combine_markdown_files(markdown_files, competitor_names)
        html_buffer = self._render_html_report_buffer(combined_markdown, title)
        return self.generate_pdf_from_html_buffer(html_buffer)

# Create a singleton instance
pdf_service = PDFService()