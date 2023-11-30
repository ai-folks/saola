from saola.interface import InterfacedConvo, SubprocessInterface, LocalFileWriteInterface
from saola.model import OpenAIGPT4TurboPreview

# [!] Use at your own risk.
#
# This assistant has access to your console shell, and also has a shortcut to write
# files to your computer. However, it will not do anything without asking.
#
# - You will see everything that the assitant tries to do.
# - You will be asked to confirm (or reject) every single action of the assistant.
# - Rejecting an action will not stop the conversation. The assistant will be informed
#   of the rejection and continue the conversation.
# - Using safety_checks=False will provide a more seamless - but less safe! - experience.

InterfacedConvo(
    OpenAIGPT4TurboPreview(api_key=input("OpenAI API Key: ")),
    interfaces=[SubprocessInterface, LocalFileWriteInterface],
    safety_checks=True
).loop()