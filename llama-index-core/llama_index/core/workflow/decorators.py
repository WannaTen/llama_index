from typing import TYPE_CHECKING, Any, Callable, List, Optional, Type

from llama_index.core.bridge.pydantic import BaseModel

from .errors import WorkflowValidationError
from .utils import is_free_function, validate_step_signature

if TYPE_CHECKING:
    from .workflow import Workflow


class StepConfig(BaseModel):
    accepted_events: List[Any]
    event_name: str
    return_types: List[Any]
    pass_context: bool
    num_workers: int


def step(
    workflow: Optional[Type["Workflow"]] = None,
    pass_context: bool = False,
    num_workers: int = 1,
):
    """Decorator used to mark methods and functions as workflow steps.

    Decorators are evaluated at import time, but we need to wait for
    starting the communication channels until runtime. For this reason,
    we temporarily store the list of events that will be consumed by this
    step in the function object itself.
    """

    def decorator(func: Callable) -> Callable:
        # If this is a free function, call add_step() explicitly.
        if is_free_function(func.__qualname__):
            if workflow is None:
                msg = f"To decorate {func.__name__} please pass a workflow class to the @step() decorator."
                raise WorkflowValidationError(msg)
            workflow.add_step(func)

        if not isinstance(num_workers, int) or num_workers <= 0:
            raise WorkflowValidationError(
                "num_workers must be an integer greater than 0"
            )

        # This will raise providing a message with the specific validation failure
        event_name, event_types, return_types = validate_step_signature(func)

        # store the configuration in the function object
        func.__step_config = StepConfig(
            accepted_events=event_types,
            event_name=event_name,
            return_types=return_types,
            pass_context=pass_context,
            num_workers=num_workers,
        )

        return func

    return decorator
