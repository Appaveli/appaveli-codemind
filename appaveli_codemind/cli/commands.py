"""
CLI commands for Appaveli CodeMind
"""

import os
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from core.agent import CodeMindAgent
from core.models import BoilerplateType, RefactorType
from utils.validation import validate_file_path, validate_api_key

console = Console()

# ASCII Art Logo for Appaveli CodeMind
LOGO = """
[bold blue]
 █████╗ ██████╗ ██████╗  █████╗ ██╗   ██╗███████╗██╗     ██╗
██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║   ██║██╔════╝██║     ██║
███████║██████╔╝██████╔╝███████║██║   ██║█████╗  ██║     ██║
██╔══██║██╔═══╝ ██╔═══╝ ██╔══██║╚██╗ ██╔╝██╔══╝  ██║     ██║
██║  ██║██║     ██║     ██║  ██║ ╚████╔╝ ███████╗███████╗██║
╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚══════╝╚═╝

 ██████╗ ██████╗ ██████╗ ███████╗███╗   ███╗██╗███╗   ██╗██████╗ 
██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗ ████║██║████╗  ██║██╔══██╗
██║     ██║   ██║██║  ██║█████╗  ██╔████╔██║██║██�██╗ ██║██║  ██║
██║     ██║   ██║██║  ██║██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
╚██████╗╚██████╔╝██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ 
[/bold blue]

[italic]Your Intelligent Code Assistant by AppaveliTech Solutions[/italic]
"""


@click.group()
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.version_option(version='0.1.0', prog_name='Appaveli CodeMind')
@click.pass_context
def cli(ctx, api_key, verbose):
    """
    Appaveli CodeMind - Your Intelligent Code Assistant
    
    AI-powered code refactoring, security scanning, and generation for Java, 
    Kotlin, Swift, C++, Dart, and JavaScript.
    """
    # Display logo on first run
    if ctx.invoked_subcommand is None:
        console.print(LOGO)
        console.print("\n[green]Welcome to Appaveli CodeMind![/green]")
        console.print("Run [bold]appaveli-codemind --help[/bold] to see all available commands.\n")
        return
    
    # Validate API key
    resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        console.print("[red]❌ Error: OpenAI API key is required.[/red]")
        console.print("Set the OPENAI_API_KEY environment variable or use --api-key option.")
        ctx.exit(1)
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['agent'] = CodeMindAgent(api_key=api_key)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print(f"[dim]Initialized Appaveli CodeMind[/dim]")


@cli.command()
@click.option('--file', '-f', required=True, help='File to analyze')
@click.option('--output', '-o', help='Output file for analysis report (JSON)')
@click.pass_context
def analyze(ctx, file, output):
    """Analyze a code file for issues, suggestions, and metrics"""
    
    if not validate_file_path(file):
        console.print(f"[red]❌ Error: File not found or not accessible: {file}[/red]")
        ctx.exit(1)
    
    agent = ctx.obj['agent']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🔍 Analyzing file...", total=None)
        
        try:
            result = agent.analyze_file(file)
        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            ctx.exit(1)
    
    # Display results
    console.print(f"\n[bold green]📊 Analysis Results for {file}[/bold green]")
    
    # Basic info table
    info_table = Table(show_header=False, box=None)
    info_table.add_row("[cyan]Language:[/cyan]", result.language.value.title())
    info_table.add_row("[cyan]Lines of code:[/cyan]", str(result.line_count))
    info_table.add_row("[cyan]Analysis time:[/cyan]", result.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    
    console.print(Panel(info_table, title="File Information", border_style="blue"))
    
    # Security issues
    if result.security_issues:
        console.print(f"\n[red]🚨 Security Issues Found ({len(result.security_issues)}):[/red]")
        
        for i, issue in enumerate(result.security_issues, 1):
            severity_color = {
                "critical": "red",
                "high": "red", 
                "medium": "yellow",
                "low": "blue",
                "info": "dim"
            }.get(issue.severity.value, "white")
            
            console.print(f"  {i}. [{severity_color}]Line {issue.line}: {issue.type.upper()}[/{severity_color}]")
            console.print(f"     {issue.description}")
            console.print(f"     💡 Fix: {issue.fix_suggestion}\n")
    else:
        console.print("\n[green]✅ No security issues found[/green]")
    
    # Save report if output specified
    if output:
        import json
        from dataclasses import asdict
        
        # Convert to dict and handle datetime serialization
        report_data = asdict(result)
        report_data['analysis_timestamp'] = result.analysis_timestamp.isoformat()
        
        with open(output, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        console.print(f"\n[green]📄 Analysis report saved to {output}[/green]")


@cli.command()
@click.option('--file', '-f', required=True, help='File to refactor')
@click.option('--type', '-t', 
              type=click.Choice([rt.value for rt in RefactorType]), 
              default='general_cleanup',
              help='Type of refactoring to perform')
@click.option('--output', '-o', help='Output file (default: overwrite original)')
@click.option('--backup', is_flag=True, help='Create backup of original file')
@click.pass_context
def refactor(ctx, file, type, output, backup):
    """Refactor code using AI-powered analysis"""
    
    if not validate_file_path(file):
        console.print(f"[red]❌ Error: File not found: {file}[/red]")
        ctx.exit(1)
    
    agent = ctx.obj['agent']
    refactor_type = RefactorType(type)
    
    # Create backup if requested
    if backup:
        from utils.file_utils import FileUtils
        backup_path = FileUtils.backup_file(file)
        console.print(f"[dim]📋 Backup created: {backup_path}[/dim]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"🔄 Refactoring with {type}...", total=None)
        
        try:
            result = agent.refactor_file(file, refactor_type, output)
        except Exception as e:
            console.print(f"[red]❌ Refactoring failed: {e}[/red]")
            ctx.exit(1)
    
    if not result.success:
        console.print(f"[red]❌ Refactoring failed: {result.error_message}[/red]")
        ctx.exit(1)
    
    # Display results
    console.print(f"[green]✅ Refactoring complete![/green]")
    
    info_table = Table(show_header=False, box=None)
    info_table.add_row("[cyan]Language:[/cyan]", result.language.value.title())
    info_table.add_row("[cyan]Refactor type:[/cyan]", result.refactor_type.value.replace('_', ' ').title())
    info_table.add_row("[cyan]Original lines:[/cyan]", str(len(result.original_code.split('\n'))))
    info_table.add_row("[cyan]Refactored lines:[/cyan]", str(len(result.refactored_code.split('\n'))))
    info_table.add_row("[cyan]Estimated cost:[/cyan]", f"${result.cost_estimate:.4f}")
    
    console.print(Panel(info_table, title="Refactoring Summary", border_style="green"))
    
    if not output:
        console.print("\n[bold]Refactored Code Preview:[/bold]")
        syntax = Syntax(
            result.refactored_code[:1000] + ("..." if len(result.refactored_code) > 1000 else ""),
            result.language.value,
            theme="monokai",
            line_numbers=True
        )
        console.print(Panel(syntax, title="Code Preview"))
        
        if click.confirm("Save refactored code to original file?"):
            from utils.file_utils import FileUtils
            FileUtils.write_file(file, result.refactored_code)
            console.print(f"[green]✅ Refactored code saved to {file}[/green]")
    else:
        console.print(f"[green]✅ Refactored code saved to {output}[/green]")


@cli.command()
@click.option('--type', '-t', required=True,
              type=click.Choice([bt.value for bt in BoilerplateType]),
              help='Type of boilerplate to generate')
@click.option('--name', '-n', required=True, help='Name for the generated component')
@click.option('--package', '-p', help='Package name (for Java/Kotlin)')
@click.option('--fields', help='Fields for data classes (format: name:type,name:type)')
@click.option('--output', '-o', help='Output file')
@click.pass_context
def generate(ctx, type, name, package, fields, output):
    """Generate boilerplate code templates"""
    
    agent = ctx.obj['agent']
    template_type = BoilerplateType(type)
    
    # Parse fields if provided
    parsed_fields = {}
    if fields:
        for field in fields.split(','):
            if ':' in field:
                field_name, field_type = field.split(':', 1)
                parsed_fields[field_name.strip()] = field_type.strip()
    
    kwargs = {
        'package': package,
        'fields': parsed_fields,
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"🏗️ Generating {type}...", total=None)
        
        try:
            result = agent.generate_boilerplate(template_type, name, output, **kwargs)
        except Exception as e:
            console.print(f"[red]❌ Generation failed: {e}[/red]")
            ctx.exit(1)
    
    if not result.success:
        console.print(f"[red]❌ Generation failed: {result.error_message}[/red]")
        ctx.exit(1)
    
    # Display results
    console.print(f"[green]✅ Generated {type}: {name}[/green]")
    
    # Display generated code
    syntax = Syntax(
        result.generated_code,
        result.language.value,
        theme="monokai",
        line_numbers=True
    )
    console.print(Panel(syntax, title=f"Generated {type}: {name}"))
    
    if output:
        console.print(f"[green]✅ Code saved to {output}[/green]")
    elif click.confirm("Save generated code to file?"):
        # Auto-generate filename based on type and language
        extension_map = {
            'java': '.java',
            'kotlin': '.kt',
            'swift': '.swift',
            'cpp': '.cpp',
            'dart': '.dart',
            'javascript': '.js',
        }
        
        extension = extension_map.get(result.language.value, '.txt')
        suggested_filename = f"{name}{extension}"
        
        filename = click.prompt("Enter filename", default=suggested_filename)
        
        from utils.file_utils import FileUtils
        FileUtils.write_file(filename, result.generated_code)
        console.print(f"[green]✅ Code saved to {filename}[/green]")


@cli.command()
@click.option('--file', '-f', required=True, help='File to generate tests for')
@click.option('--type', '-t', default='unit', 
              type=click.Choice(['unit', 'integration']),
              help='Type of tests to generate')
@click.option('--output', '-o', help='Output file for tests')
@click.pass_context
def test(ctx, file, type, output):
    """Generate unit or integration tests for code files"""
    
    if not validate_file_path(file):
        console.print(f"[red]❌ Error: File not found: {file}[/red]")
        ctx.exit(1)
    
    agent = ctx.obj['agent']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"🧪 Generating {type} tests...", total=None)
        
        try:
            test_code = agent.generate_tests(file, type, output)
        except Exception as e:
            console.print(f"[red]❌ Test generation failed: {e}[/red]")
            ctx.exit(1)
    
    if not test_code:
        console.print("[red]❌ No tests were generated[/red]")
        ctx.exit(1)
    
    # Detect language for syntax highlighting
    language = agent.language_detector.detect(file)
    lang_str = language.value if language else "text"
    
    console.print(f"[green]✅ Generated {type} tests for {file}[/green]")
    
    # Display generated tests
    syntax = Syntax(test_code, lang_str, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {type.title()} Tests"))
    
    if output:
        console.print(f"[green]✅ Tests saved to {output}[/green]")


@cli.command()
@click.option('--project', '-p', required=True, help='Project directory to scan')
@click.option('--output', '-o', help='Output file for security report (JSON)')
@click.pass_context
def security(ctx, project, output):
    """Perform comprehensive security scan of project"""
    
    if not os.path.exists(project):
        console.print(f"[red]❌ Error: Project directory not found: {project}[/red]")
        ctx.exit(1)
    
    agent = ctx.obj['agent']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🔒 Scanning project security...", total=None)
        
        try:
            result = agent.scan_project_security(project)
        except Exception as e:
            console.print(f"[red]❌ Security scan failed: {e}[/red]")
            ctx.exit(1)
    
    # Display security summary
    console.print(f"\n[bold red]🔒 Security Scan Results for {project}[/bold red]")
    
    summary_table = Table(title="Security Summary")
    summary_table.add_column("Category", style="cyan")
    summary_table.add_column("Count", style="magenta")
    summary_table.add_column("High/Critical", style="red")
    
    summary_table.add_row(
        "Code Issues",
        str(result.summary.get('total_code_issues', 0)),
        str(result.summary.get('high_severity_issues', 0))
    )
    
    console.print(summary_table)
    
    # Show detailed issues
    if result.code_issues:
        console.print(f"\n[red]🚨 Code Security Issues:[/red]")
        
        for i, issue in enumerate(result.code_issues[:10], 1):  # Show first 10
            console.print(f"  {i}. [red]{issue.type}[/red] in {os.path.basename(issue.file_path or '')}")
            console.print(f"     Line {issue.line}: {issue.description}")
            console.print(f"     💡 {issue.fix_suggestion}\n")
        
        if len(result.code_issues) > 10:
            console.print(f"     ... and {len(result.code_issues) - 10} more issues")
    
    # Save report if requested
    if output:
        import json
        from dataclasses import asdict
        
        report_data = asdict(result)
        report_data['scan_timestamp'] = result.scan_timestamp.isoformat()
        
        with open(output, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        console.print(f"\n[green]📄 Security report saved to {output}[/green]")


@cli.command()
def version():
    """Show Appaveli CodeMind version information"""
    from version import __version__, __author__, __description__
    
    console.print(LOGO)
    console.print(f"[bold]Version:[/bold] {__version__}")
    console.print(f"[bold]Author:[/bold] {__author__}")
    console.print(f"[bold]Description:[/bold] {__description__}")


@cli.command()
def info():
    """Show system information and supported languages"""
    from core.language_detector import LanguageDetector
    
    console.print("[bold blue]📋 Appaveli CodeMind System Information[/bold blue]\n")
    
    # Supported languages
    languages_table = Table(title="Supported Languages")
    languages_table.add_column("Language", style="cyan")
    languages_table.add_column("Extensions", style="magenta")
    languages_table.add_column("Features", style="green")
    
    for lang in LanguageDetector.get_supported_languages():
        extensions = [ext for ext, l in LanguageDetector.EXTENSIONS.items() if l == lang]
        features = "Analysis, Refactoring, Generation, Security, Tests"
        
        languages_table.add_row(
            lang.value.title(),
            ", ".join(extensions),
            features
        )
    
    console.print(languages_table)


if __name__ == '__main__':
    cli()