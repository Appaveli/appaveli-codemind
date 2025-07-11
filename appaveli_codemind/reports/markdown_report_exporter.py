from appaveli_codemind.core.models import AnalysisResult
from pathlib import Path

class MarkdownReportExporter:
    @staticmethod
    def export(result: AnalysisResult) -> str:
        lines = [
            f"# 📄 Code Analysis Report: `{Path(result.file_path).name}`",
            "",
            "## 🧾 Summary",
            f"- **Language:** {result.language.value.title()}",
            f"- **Lines of Code:** {result.line_count}",
            f"- **Timestamp:** {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        # Optional code summary
        if result.summary:
            lines.append("## 📘 Code Summary")
            lines.append(result.summary.strip())
            lines.append("")

        if result.security_issues:
            lines.append("## 🚨 Security Issues")
            for i, issue in enumerate(result.security_issues, 1):
                lines.extend([
                    f"### {i}. {issue.type.title()} (Line {issue.line})",
                    f"- **Severity:** `{issue.severity.value.upper()}`",
                    f"- **Description:** {issue.description}",
                    f"- **Fix Suggestion:** {issue.fix_suggestion}",
                    ""
                ])
        else:
            lines.append("✅ No security issues found.")

        return "\n".join(lines)