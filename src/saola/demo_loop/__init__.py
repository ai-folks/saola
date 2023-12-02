from saola.convo import Convo, ShellInterface, FileWriteInterface
from saola.model import OpenAIGPT4TurboPreview
from rich.panel import Panel
from rich import print as rprint
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
    return Convo(
        OpenAIGPT4TurboPreview(api_key=os.getenv("OPENAI_API_KEY") or input("OpenAI API Key: ")),
        interfaces=[ShellInterface, FileWriteInterface],
        safety_checks=True
    ).loop()