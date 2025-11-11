"""User state management for conversation flow"""
from typing import Optional

# Store user states: {user_id: state_string}
user_states: dict[int, str] = {}


def set_state(user_id: int, state: str):
    """Set user state"""
    user_states[user_id] = state


def get_state(user_id: int) -> Optional[str]:
    """Get user state"""
    return user_states.get(user_id)


def clear_state(user_id: int):
    """Clear user state"""
    if user_id in user_states:
        del user_states[user_id]


def check_state(user_id: int, state_prefix: str) -> bool:
    """Check if user is in specific state"""
    state = get_state(user_id)
    return state is not None and state.startswith(state_prefix)

