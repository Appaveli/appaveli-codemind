from appaveli_codemind.core.models import AnalysisResult
from jinja2 import Template
from pathlib import Path

class HtmlReportExporter:
    @staticmethod
    def export(result: AnalysisResult) -> str:
        template_str = Path("reports/templates/html_report_template.html").read_text(encoding="utf-8")

        template = Template(template_str)

        rendered = template.render(
            filename=Path(result.file_path).name,
            language=result.language.value.title(),
            line_count=result.line_count,
            timestamp=result.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            issues=result.security_issues
        )

        return rendered 
