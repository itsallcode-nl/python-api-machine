from dataclasses import dataclass, field, InitVar

STATE_WILDCARD = "*"


@dataclass
class Transition:
    state: str
    action: str
    target: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ScopedTransition(Transition):
    scope: InitVar[callable] = None

    def __post_init__(self, scope):
        self.metadata['scoped'] = dict(
            fields=scope
        )


class StateMachine:
    def __init__(self, transitions=None):
        self.transitions = transitions or []

    def __getitem__(self, key):
        state, action = key
        for transition in self.transitions:
            if transition.state not in [STATE_WILDCARD, state]:
                continue

            if transition.action != action:
                continue

            return transition

        raise KeyError(f"No transition {action} on {state=}")

    def do(self, current_state, action):
        try:
            return self[current_state, action]
        except IndexError:
            raise ValueError(
                f"Invalid action {action} on state {current_state}"
            )


CrudLifeCycle = [
    Transition(None, 'create', 'active'),
    ScopedTransition('active', 'update', 'active', scope=lambda e: e.fields(e.mutable.union(e.key))),
    Transition('active', 'delete', 'deleted'),
]
