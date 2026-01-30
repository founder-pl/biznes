from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ShellContext:
    _path: List[str] = field(default_factory=lambda: ["biznes"])
    _game_active: bool = False

    def reset_to_main(self) -> None:
        self._game_active = False
        self._path = ["biznes"]

    def enter_game(self) -> None:
        self._game_active = True
        self._path = ["biznes", "gra"]

    def enter_actions(self) -> None:
        if self._game_active:
            self._path = ["biznes", "gra", "akcje"]

    def enter_action(self, action_id: str) -> None:
        if self._game_active:
            self._path = ["biznes", "gra", "akcje", action_id]

    def reset_to_game(self) -> None:
        if self._game_active:
            self._path = ["biznes", "gra"]

    def go_back(self) -> bool:
        if len(self._path) > 1:
            self._path.pop()
            if self._path == ["biznes"]:
                self._game_active = False
            return True
        return False

    def get_prompt(self) -> str:
        return "/".join(self._path) + "> "

    @property
    def in_game(self) -> bool:
        return self._game_active

    @property
    def in_actions(self) -> bool:
        return "akcje" in self._path

    @property
    def current_action(self) -> Optional[str]:
        if len(self._path) >= 4 and self._path[-2] == "akcje":
            return self._path[-1]
        return None
