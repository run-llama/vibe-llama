# Human-in-the-Loop Flight Booking Workflow Example

This workflow demonstrates how to build a human-in-the-loop, event-driven workflow for flight search and booking using [llama-index-workflows](https://github.com/run-llama/llama-index-workflows). The workflow uses an LLM to extract flight details from user input, presents flight options, and requires human approval before booking.

## Installation

Install all required dependencies (including llama-index-workflows and OpenAI LLM support):

```bash
pip install -e .
```

## Usage

Run the workflow from the command line:

```bash
python workflow.py \
  --message "I want to fly from San Francisco to Paris on July 10th"
```

**Note:**

- You must set your `OPENAI_API_KEY` in the environment before running.

## Workflow Overview

- **search_for_flight**:
  Uses an LLM to extract flight details from the user's message and searches for available flights.
  Emits a `FlightSearchEvent` with candidate flights.

- **chosen_flight**:
  Waits for human input to select a flight and confirm booking.
  Books the flight if approved, or exits if declined.

## Human-in-the-Loop Pattern

- The workflow pauses to request human input for flight selection and booking approval.
- Input is provided interactively via the command line.

## Customization

- Replace the `FlightsAPI` logic with your own flight search and booking implementation.
- Extend the workflow to support additional validation or multi-step approval.

## References

- [llama-index-workflows documentation](https://github.com/run-llama/llama-index-workflows)
