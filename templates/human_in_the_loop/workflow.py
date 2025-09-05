import random

from pydantic import BaseModel, Field
from workflows import Workflow, step, Context
from workflows.resource import Resource
from typing import Annotated
from workflows.events import (
    StartEvent,
    StopEvent,
    InputRequiredEvent,
    HumanResponseEvent,
)

from llama_index.llms.openai import OpenAIResponses
from llama_index.core.llms import ChatMessage
from llama_index.core.llms.structured_llm import StructuredLLM


# replace with an actual flight searcher
class FlightsAPI:
    def __init__(self) -> None:
        self.allowed_departure = [
            "San Francisco",
            "San Jose",
            "Los Angeles",
            "New York",
        ]
        self.allowed_arrival = ["Paris", "London", "Berlin", "Rome"]
        self.allowed_hours = ["7.00 AM", "12.00 AM", "5.00 PM", "10.00 PM"]

    def search_flights(
        self, departure: str, arrival: str, date: str
    ) -> str | list[str]:
        if arrival not in self.allowed_arrival:
            return "Sorry, we do not have planes that go to " + arrival
        if departure not in self.allowed_departure:
            return "Sorry, we do not have planes departing from " + departure
        allowed_hours = self.allowed_hours[self.allowed_departure.index(departure) :]
        flights = []
        for hour in allowed_hours:
            flights.append(
                f"Flight from {departure} to {arrival} at {hour} on {date} for {random.randint(200, 400)}$"
            )
        return flights

    def book_flight(self, flight: str) -> str:
        n = random.randint(0, 1)
        if n == 0:
            return f"Successfully booked: {flight}"
        return "Sorry, something went wrong while booking your flight"


class FlightSearchEvent(InputRequiredEvent):
    candidate_flights: list[str]


class FlightChoiceEvent(HumanResponseEvent):
    chosen_flight: str
    continue_booking: bool


async def get_flights_api(*args, **kwargs) -> FlightsAPI:
    return FlightsAPI()


class FlightSearchDetails(BaseModel):
    departure_location: str = Field(description="Departure location")
    arrival_location: str = Field(description="Arrival location")
    date: str = Field(description="Flight date")


async def get_llm(*args, **kwargs) -> StructuredLLM:
    return OpenAIResponses("gpt-4.1").as_structured_llm(FlightSearchDetails)


class FlightSearchWorkflow(Workflow):
    @step
    async def search_for_flight(
        self,
        ev: StartEvent,
        ctx: Context,
        llm: Annotated[StructuredLLM, Resource(get_llm)],
        flight_api: Annotated[FlightsAPI, Resource(get_flights_api)],
    ) -> StopEvent | FlightSearchEvent:
        response = await llm.achat(
            [
                ChatMessage(
                    content=f"Extract flight details from this request: {ev.message}"
                )
            ]
        )
        if response.message.content:
            flight_details = FlightSearchDetails.model_validate_json(
                response.message.content
            )
        else:
            return StopEvent(result="Unable to get details for your flight")
        flights = flight_api.search_flights(
            departure=flight_details.departure_location,
            arrival=flight_details.arrival_location,
            date=flight_details.date,
        )
        if isinstance(flights, str):
            return StopEvent(result=flights)
        else:
            return FlightSearchEvent(candidate_flights=flights)

    @step
    async def chosen_flight(
        self,
        ev: FlightChoiceEvent,
        flight_api: Annotated[FlightsAPI, Resource(get_flights_api)],
        ctx: Context,
    ) -> StopEvent:
        if ev.continue_booking:
            booking = flight_api.book_flight(ev.chosen_flight)
            return StopEvent(result=booking)
        else:
            return StopEvent(result="No permission to book, exiting...")


async def main(message: str) -> None:
    w = FlightSearchWorkflow(timeout=100, verbose=False)
    handler = w.run(message=message)
    async for ev in handler.stream_events():
        if isinstance(ev, FlightSearchEvent):
            print("Flights:\n" + "\n- ".join(ev.candidate_flights) + "\n\n")
            are_ok = input("Are the flights ok for you? [yes/no] ")
            if are_ok.lower().strip() != "yes":
                handler.ctx.send_event(
                    FlightChoiceEvent(chosen_flight="", continue_booking=False)
                )  # type: ignore
                break
            res = input("Choose a flight: ")
            while res not in ev.candidate_flights:
                res = input(
                    "Sorry, that flight is not available, can you choose one flight from the above, please? Your choice: "
                )
            appr = input(f"Do you wish to continue with booking for {res}? [yes/no] ")
            if appr.lower().strip() == "yes":
                handler.ctx.send_event(
                    FlightChoiceEvent(chosen_flight=res, continue_booking=True)
                )  # type: ignore
            else:
                handler.ctx.send_event(
                    FlightChoiceEvent(chosen_flight=res, continue_booking=False)
                )  # type: ignore
    result = await handler
    print(str(result))


if __name__ == "__main__":
    import asyncio
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-m", "--message", required=True, help="Flight you would like to take"
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY", None):
        raise ValueError(
            "You need to set OPENAI_API_KEY in your environment before using this workflow"
        )

    asyncio.run(main(message=args.message))
