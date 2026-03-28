import typer
import os
from dotenv import load_dotenv
from rich.console import Console
from llm.engine import MultiProviderLLM, should_use_local

load_dotenv()
console = Console()
app = typer.Typer()

@app.command()
def generate(prompt: str, output: str = "generated_code.py", test: bool = True):
    """Generate code and optionally create a test script."""
    engine = MultiProviderLLM()
    
    # Auto-switch logic
    force_local = should_use_local(prompt) and os.getenv("LLM_MODE") != "CLOUD_ONLY"
    if force_local:
        console.print("[yellow]⚡ Simple task detected: Routing to Local LLM[/yellow]")
        # Hack to force ollama for demo if keys exist but task is simple
        original_mode = os.getenv("LLM_MODE")
        os.environ["LLM_MODE"] = "LOCAL_ONLY"
        engine = MultiProviderLLM()
    
    console.print(f"🧠 Generating with {engine.provider.upper()}...")
    code = engine.generate(prompt)
    
    # Save Main Code
    with open(output, "w", encoding='utf-8') as f:
        f.write(code)
    console.print(f"[green]✅ Saved code to {output}[/green]")
    
    # Generate Test Script if requested
    if test:
        test_prompt = f"Write a pytest unit test suite for the following code:\n\n{code}"
        console.print("🧪 Generating test script...")
        test_code = engine.generate(test_prompt, system_prompt="You are an expert tester. Write only pytest code.")
        
        test_filename = f"test_{output}"
        with open(test_filename, "w", encoding='utf-8') as f:
            f.write(test_code)
        console.print(f"[blue]✅ Saved test suite to {test_filename}[/blue]")
        console.print(f"💡 Run tests with: [bold]pytest {test_filename}[/bold]")

@app.command()
def status():
    engine = MultiProviderLLM()
    console.print(f"[bold green]✅ Active Provider: {engine.provider.upper()}[/bold green]")
    if engine.provider == "ollama":
        console.print("🏠 Running Locally (Private & Free)")
    else:
        console.print("☁️ Running on Cloud (High Performance)")

if __name__ == "__main__":
    app()
