import typer
from mock.mock_runner import MockRunner
app = typer.Typer()
@app.command()
def status(): MockRunner().show_status()
@app.command()
def generate(prompt: str): MockRunner().run_generation(prompt)
@app.command()
def interactive(): MockRunner().run_interactive()
if __name__ == "__main__": app()
