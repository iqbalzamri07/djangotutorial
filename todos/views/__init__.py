from .about import about
from .activity import activity
from .calendar import calendar, calendar_add
from .crud import delete, edit, edit_todos, restore_todo
from .home import home
from .search import search_todos

__all__ = [
    "about",
    "activity",
    "calendar",
    "calendar_add",
    "delete",
    "edit",
    "edit_todos",
    "home",
    "restore_todo",
    "search_todos",
]
