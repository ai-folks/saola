from saola.convo import Convo, ShellInterface, FileWriteInterface
from saola.model import OpenAIModel
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint
from openai import OpenAI
import os

# [!] Use at your own risk.
#
# This assistant showcases Saola's built-in capabilities. Currently:
# - The "subprocess" interface.
# - The "local file write" interface.
# - The preview version of OpenAI's GPT-4 turbo model.
#
# This assistant has access to your shell console, and also has a shortcut to write
# files to your computer. However, it will not do anything without asking.
#
# - You will see everything that the assitant tries to do.
# - You will be asked to confirm (or reject) every single action of the assistant.
# - Rejecting an action will not stop the conversation. The assistant will be informed
#   of the rejection and continue the conversation.
# - Using safety_checks=False will provide a more seamless - but less safe! - experience.
#
# This file is likely to experience lots of breaking changes in the future.
# Do not have your project depend on it.

def demo_loop():
    rprint(Panel("[red1] [!] This assistant will be able to execute commands\n" +
                        "    on your shell when prompted. You will be asked to\n" +
                        "    confirm the execution of each of these commands.\n" + 
                        "    Please read each command and respond carefully.\n" +
                        "    Use at your own risk.[/red1]", border_style="red1"))
    
    open_ai_api_key = os.getenv("OPENAI_API_KEY") or input("OpenAI API Key: ")
    open_ai_api_base = os.getenv("OPENAI_API_BASE")
    client = OpenAI(api_key=open_ai_api_key, base_url=open_ai_api_base)
    available_model_names = [model.id for model in client.models.list()]
    preferred_model_names = ["gpt-4-1106-preview", "gpt-4", "gpt-3.5-turbo-1106"]
    model_name = None
    for name in preferred_model_names:
        if name not in available_model_names: continue
        model_name = name
        break
    if model_name is None:
        model_name = Prompt.ask("Choose an OpenAI model", choices=available_model_names)
    rprint(Panel("Using OpenAI model [bold]" + model_name + "[/bold]"))
    return Convo(
        OpenAIModel(model_name, client=client),
        interfaces=[ShellInterface, FileWriteInterface],
        safety_checks=True
    ).loop()