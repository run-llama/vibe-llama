from pydantic import BaseModel, ConfigDict
from workflows import Workflow, step, Context
from workflows.events import (
    Event,
    StartEvent,
    StopEvent,
)
from typing import Annotated, Optional
from workflows.resource import Resource
from llama_index.llms.openai import OpenAI


# replace with an actual email sending client
class EmailClient:
    def __init__(self, sender_email: str):
        if not self._internal_email(sender_email):
            print("Sorry, you are not allowed to use this email client")
            return
        self.sender_email = sender_email

    def send(self, receiver_email: str, subject: str, content: str) -> bool:
        if not self._internal_email(receiver_email):
            print(
                "Sorry, we cannot send an email to a person outside of the organization"
            )
            return False
        print(
            f"Sent an email from {self.sender_email} to {receiver_email} with subject '{subject}' and content:\n{content}"
        )
        return True

    def _internal_email(self, email: str) -> bool:
        return email.endswith("@mycompany.com")


class EmailStats:
    def __init__(self):
        self.success = 0
        self.fail = 0

    def update(self, result: bool):
        if result:
            self.success += 1
        else:
            self.fail += 1


class PrepareEmail(Event):
    receiver: str
    subject: str
    content: str


class SendEmail(Event):
    success: bool


class EmailFlowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    email_num: int = 0
    email_client: Optional[EmailClient] = None


async def get_llm(*args, **kwargs) -> OpenAI:
    return OpenAI("gpt-4.1")


async def get_email_stats(*args, **kwargs) -> EmailStats:
    return EmailStats()


class EmailFlow(Workflow):
    @step
    async def prepare_email(
        self,
        ev: StartEvent,
        ctx: Context[EmailFlowState],
        llm: Annotated[OpenAI, Resource(get_llm)],
    ) -> PrepareEmail | StopEvent | None:
        async with ctx.store.edit_state() as state:
            cl = EmailClient(sender_email=ev.sender)
            if hasattr(cl, "sender_email"):
                state.email_client = cl
                state.email_num = len(ev.receivers)
            else:
                return StopEvent(
                    result="It is not possible to send emails from your current address: please use a mycompany.com address and try again."
                )
        email_content = await llm.acomplete(
            f"Given this email draft: {ev.draft} and subject: {ev.subject}, can you please create an fully-formed email message to send?"
        )
        for receiver in ev.receivers:
            ctx.send_event(
                PrepareEmail(
                    receiver=receiver, subject=ev.subject, content=email_content.text
                )
            )

    @step
    async def send_email(
        self,
        ev: PrepareEmail,
        ctx: Context[EmailFlowState],
        stats: Annotated[EmailStats, Resource(get_email_stats)],
    ) -> SendEmail:
        state = await ctx.store.get_state()
        succ = state.email_client.send(ev.receiver, ev.subject, ev.content)  # type: ignore
        stats.update(succ)
        return SendEmail(success=succ)

    @step
    async def collect_email_stats(
        self,
        ev: SendEmail,
        ctx: Context[EmailFlowState],
        stats: Annotated[EmailStats, Resource(get_email_stats)],
    ) -> StopEvent | None:
        state = await ctx.store.get_state()
        evs = ctx.collect_events(ev, [SendEmail] * state.email_num)
        if evs:
            return StopEvent(
                result=f"Sent {stats.success} emails, failed to send {stats.fail} emails"
            )


async def main(sender: str, receivers: list[str], subject: str, draft: str) -> None:
    w = EmailFlow(timeout=60, verbose=False)
    result = await w.run(
        sender=sender, receivers=receivers, subject=subject, draft=draft
    )
    print(str(result))


if __name__ == "__main__":
    import asyncio
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-s",
        "--sender",
        required=True,
        help="Sender email (must end with @mycompany.com)",
    )
    parser.add_argument(
        "-r",
        "--receiver",
        required=True,
        action="append",
        help="Email for the receiver (must end with @mycompany.com). Can be repeated",
    )
    parser.add_argument("-t", "--subject", required=True, help="Subject of the email")
    parser.add_argument("-d", "--draft", required=True, help="Draft for the email")

    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY", None):
        raise ValueError(
            "You need to set OPENAI_API_KEY in your environment before using this workflow"
        )

    asyncio.run(
        main(
            sender=args.sender,
            receivers=args.receiver,
            subject=args.subject,
            draft=args.draft,
        )
    )
