import abc
import os
from rich.panel import Panel
from rich import print as rprint
from rich.markup import escape
from rich.prompt import Confirm

class Console(abc.ABC):
    # A console is a bridge for the application to communicate with the user.
    def display_interface_output(self, output):
        # Displays an interface's output to the user.
        pass
    def safety_confirmation(self, question):
        # Asks the user a yes/no question and returns the answer.
        pass
    def no_safety_confirmation(self):
        # Return True always after any preparation for displaying results without a confirmation.
        pass
    def display_user_header(self):
        # Preparation for requesting the user's input.
        pass
    def get_user_input(self):
        # Gets the user's input.
        pass
    def display_assistant_header(self):
        # Preparation for displaying the assistant's output.
        pass
    def append_to_assistant_output(self, author, chunk, ending):
        # Appends text to the assistant's output.
        pass

class LocalShellConsole(Console):
    def display_interface_output(self, output):
        rprint(Panel("[bright_magenta]" + escape(output) + "[/bright_magenta]", border_style="bright_magenta"))

    def safety_confirmation(self, question):
        print("")
        rprint(Panel("[red1] SAFETY CHECK [/red1]", border_style="red1"))
        return Confirm.ask(f"[red1] {question} [/red1]")

    def no_safety_confirmation(self):
        print("")
        return True 

    def display_user_header(self):
        rprint(Panel("[bold green]USER (enter your question below)[/bold green]"))

    def get_user_input(self):
        return input("")

    def display_assistant_header(self):
        rprint(Panel("[bold blue]ASSISTANT[/bold blue]"))

    def append_to_assistant_output(self, author, chunk, ending):
        print(chunk or "", end="\n" if ending else "")
    