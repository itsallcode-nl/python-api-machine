from dataclasses import dataclass


@dataclass
class Transition:
    state: str
    action: str
    target: str
    metadata: dict = None


class StateMachine:
    def __init__(self, transitions=None):
        self.transitions = transitions or []

    def do(self, current_state, action):
        for transition in self.transitions:
            if transition.state != current_state:
                continue

            if transition.action != action:
                continue

            return transition

        raise ValueError(
            f"Invalid action {action} on state {current_state}"
        )


CrudLifeCycle = [
    Transition(None, 'create', 'active'),
    Transition('active', 'update', 'active'),
    Transition('active', 'delete', 'deleted'),
]
