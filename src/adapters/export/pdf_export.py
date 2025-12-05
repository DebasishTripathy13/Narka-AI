"""PDF export adapter."""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import io

from ...core.interfaces.export import ExportProvider
from ...core.entities.investigation import Investigation


class PDFExporter(ExportProvider):
    """
    PDF export implementation.
    
    Exports investigation data as formatted PDF report.
    """
    
    @property
    def format_name(self) -> str:
        return "pdf"
    
    @property
    def file_extension(self) -> str:
        return ".pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    def export(
        self,
        investigation: Investigation,
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export investigation to PDF file."""
        try:
            pdf_bytes = self.export_bytes(investigation, options)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "wb") as f:
                f.write(pdf_bytes)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def export_bytes(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export investigation to PDF bytes."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, ListFlowable, ListItem
            )
            
            return self._generate_pdf_reportlab(investigation, options)
        except ImportError:
            # Fallback to simple text-based PDF if reportlab not available
            return self._generate_simple_pdf(investigation, options)
    
    def _generate_pdf_reportlab(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate PDF using ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak
        )
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkblue,
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("Robin OSINT Investigation Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Investigation Summary
        elements.append(Paragraph("Investigation Summary", heading_style))
        
        summary_data = [
            ["Investigation ID:", investigation.id],
            ["Query:", investigation.query],
            ["Status:", investigation.status.value],
            ["Created:", investigation.created_at.strftime("%Y-%m-%d %H:%M:%S") if investigation.created_at else "N/A"],
            ["Search Results:", str(len(investigation.search_results))],
            ["Pages Scraped:", str(len(investigation.scraped_content))],
            ["Entities Found:", str(len(investigation.extracted_entities))],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # AI Summary
        if investigation.summary:
            elements.append(Paragraph("AI Analysis Summary", heading_style))
            elements.append(Paragraph(investigation.summary, styles['Normal']))
            elements.append(Spacer(1, 20))
        
        # Extracted Entities
        if investigation.extracted_entities:
            elements.append(Paragraph("Extracted Entities", heading_style))
            
            # Group entities by type
            entities_by_type = {}
            for entity in investigation.extracted_entities:
                etype = entity.entity_type
                if etype not in entities_by_type:
                    entities_by_type[etype] = []
                entities_by_type[etype].append(entity.value)
            
            entity_data = [["Type", "Values Found"]]
            for etype, values in entities_by_type.items():
                unique_values = list(set(values))[:10]  # Limit to 10 per type
                entity_data.append([etype, ", ".join(unique_values)])
            
            entity_table = Table(entity_data, colWidths=[1.5*inch, 4.5*inch])
            entity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('WORDWRAP', (1, 1), (1, -1), True),
            ]))
            elements.append(entity_table)
            elements.append(Spacer(1, 20))
        
        # Search Results (top 20)
        if investigation.search_results:
            elements.append(PageBreak())
            elements.append(Paragraph("Search Results (Top 20)", heading_style))
            
            results_data = [["#", "Title", "URL"]]
            for i, result in enumerate(investigation.search_results[:20], 1):
                title = result.title[:50] + "..." if len(result.title) > 50 else result.title
                url = result.url[:60] + "..." if len(result.url) > 60 else result.url
                results_data.append([str(i), title, url])
            
            results_table = Table(results_data, colWidths=[0.4*inch, 2.5*inch, 3.1*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(results_table)
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_text = f"Generated by Robin Dark Web OSINT Tool on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elements.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        return buffer.getvalue()
    
    def _generate_simple_pdf(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate a simple text-based fallback."""
        # If reportlab is not available, generate a plain text report
        lines = [
            "ROBIN OSINT INVESTIGATION REPORT",
            "=" * 50,
            "",
            f"Investigation ID: {investigation.id}",
            f"Query: {investigation.query}",
            f"Status: {investigation.status.value}",
            f"Created: {investigation.created_at}",
            f"Search Results: {len(investigation.search_results)}",
            f"Pages Scraped: {len(investigation.scraped_content)}",
            f"Entities Found: {len(investigation.extracted_entities)}",
            "",
            "=" * 50,
            "Note: Install reportlab for proper PDF generation",
            "pip install reportlab",
        ]
        
        return "\n".join(lines).encode("utf-8")
