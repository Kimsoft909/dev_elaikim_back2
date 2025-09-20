"""
CV Generation service using Django templates + WeasyPrint (full file).
"""
import logging
import yaml
import os
from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string
from io import BytesIO

logger = logging.getLogger(__name__)

# WeasyPrint import
try:
    from weasyprint import HTML, CSS
except Exception as e:
    # Raise a clear error at import time so you know to install WeasyPrint + system deps
    raise ImportError(
        "WeasyPrint is required for HTML->PDF rendering. "
        "Install via pip: pip install WeasyPrint and ensure system libraries (cairo, pango, gdk-pixbuf) are available."
    ) from e


class CVGeneratorService:
    """
    CV Generation service that:
      - loads CV data from YAML
      - renders HTML templates for preview
      - converts the rendered HTML to PDF using WeasyPrint (so PDF matches the HTML template)
    """

    def __init__(self):
        self.cv_data = self.load_cv_data()
        # kept themes map for backward compatibility (templates named cv/<theme>.html)
        self.themes = {
            "professional": "professional",
            "modern": "modern",
            "minimal": "minimal",
        }

    def load_cv_data(self):
        """Load CV data from YAML file at <BASE_DIR>/cv_data.yaml."""
        cv_data_path = Path(settings.BASE_DIR) / "cv_data.yaml"
        try:
            with open(cv_data_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
                logger.info(f"CV data loaded successfully: {type(data)} keys={list(data.keys())}")
                return data
        except Exception as e:
            logger.error(f"Failed to load CV data: {e}")
            return {}

    # -------------------------
    # HTML rendering (preview)
    # -------------------------
    def generate_html_cv(self, theme="professional"):
        """
        Render the Django template to an HTML string.
        Template expected at: templates/cv/<theme>.html
        Context exposes 'cv_data' and common subkeys for convenience.
        """
        try:
            template_name = f"cv/{theme}.html"
            context = {
                "cv_data": self.cv_data,
                "personal_info": self.cv_data.get("personal_info", {}),
                "summary": self.cv_data.get("summary", ""),
                "experience": self.cv_data.get("experience", []),
                "education": self.cv_data.get("education", []),
                "skills": self.cv_data.get("skills", {}),
                "projects": self.cv_data.get("projects", []),
                "certifications": self.cv_data.get("certifications", []),
                "languages": self.cv_data.get("languages", []),
                "interests": self.cv_data.get("interests", []),
            }

            html_content = render_to_string(template_name, context)
            logger.info(f"CV HTML generated successfully with theme: {theme}")
            return html_content

        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            raise Exception(f"Failed to generate CV HTML: {str(e)}") from e

    # -------------------------
    # PDF generation (WeasyPrint)
    # -------------------------
    def generate_pdf(self, theme="professional", base_url=None, presentational_hints=True):
        """
        Generate a PDF from the rendered HTML using WeasyPrint.

        Args:
            theme (str): template theme name (templates/cv/<theme>.html)
            base_url (str|None): base URL used by WeasyPrint to resolve relative links and static files.
                - If you pass an absolute URL (e.g. request.build_absolute_uri('/')), pass that string.
                - If None, this function will try the following fallbacks in order:
                    1. settings.STATIC_ROOT (converted to file:// path if it's a filesystem path)
                    2. first entry of settings.STATICFILES_DIRS (if defined)
                    3. settings.BASE_DIR / 'static'
                WeasyPrint accepts either a web URL or a file:// path.
            presentational_hints (bool): pass to WeasyPrint; keep True to honor CSS presentational hints.
        Returns:
            bytes: PDF binary data
        Raises:
            Exception on failure
        """
        try:
            # Render HTML from template
            html_string = self.generate_html_cv(theme)

            # Determine base_url fallback if not provided
            effective_base = base_url
            if not effective_base:
                # Prefer STATIC_ROOT if set and not empty
                static_root = getattr(settings, "STATIC_ROOT", None)
                if static_root:
                    # Use filesystem path with file:// scheme
                    effective_base = Path(static_root).absolute().as_uri()
                else:
                    # Try STATICFILES_DIRS
                    sdirs = getattr(settings, "STATICFILES_DIRS", [])
                    if sdirs:
                        effective_base = Path(sdirs[0]).absolute().as_uri()
                    else:
                        # Fallback to <BASE_DIR>/static
                        fallback = Path(settings.BASE_DIR) / "static"
                        effective_base = fallback.absolute().as_uri()

            # Prepare WeasyPrint HTML object
            html_obj = HTML(string=html_string, base_url=effective_base)

            # Optionally you can provide a CSS file or list of CSS objects:
            # css_path = Path(settings.BASE_DIR) / 'static' / 'cv' / 'pdf.css'  # if you maintain separate CSS
            # css = CSS(filename=str(css_path)) if css_path.exists() else None

            buffer = BytesIO()
            # Write PDF; let WeasyPrint handle styles, images (via base_url), fonts, etc.
            html_obj.write_pdf(target=buffer, presentational_hints=presentational_hints)

            pdf_data = buffer.getvalue()
            buffer.close()

            logger.info("PDF generated via WeasyPrint successfully")
            return pdf_data

        except Exception as e:
            logger.error(f"WeasyPrint PDF generation failed: {e}", exc_info=True)
            raise Exception(f"Failed to generate PDF via WeasyPrint: {str(e)}") from e

    # kept as placeholders if you still want programmatic ReportLab fallback (not used)
    def professional_theme(self):
        """Deprecated: kept for compatibility but now we use template->WeasyPrint."""
        # If someone still calls professional_theme directly, render PDF from template
        return self.generate_pdf(theme="professional")

    def modern_theme(self):
        return self.generate_pdf(theme="modern")

    def minimal_theme(self):
        return self.generate_pdf(theme="minimal")


# Global service instance
cv_service = CVGeneratorService()
