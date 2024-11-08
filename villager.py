#
# villager.py
#
# Copyright 2022 OTSUKI Takashi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
from typing import Dict, List

from aiwolf import (
    AbstractPlayer,
    Agent,
    Content,
    GameInfo,
    GameSetting,
    Judge,
    Role,
    Species,
    Status,
    Talk,
    Topic,
    VoteContentBuilder,
)
from aiwolf.constant import AGENT_NONE

from const import CONTENT_SKIP


class SampleVillager(AbstractPlayer):
    """Sample villager agent."""

    me: Agent
    """Myself."""
    vote_candidate: Agent
    """Candidate for voting."""
    game_info: GameInfo
    """Information about current game."""
    game_setting: GameSetting
    """Settings of current game."""
    comingout_map: Dict[Agent, Role]
    """Mapping between an agent and the role it claims that it is."""
    divination_reports: List[Judge]
    """Time series of divination reports."""
    identification_reports: List[Judge]
    """Time series of identification reports."""
    talk_list_head: int
    """Index of the talk to be analysed next."""

    def __init__(self) -> None:
        """Initialize a new instance of SampleVillager."""
        with open("../aiwolf24/playground/log.txt","w"):
            pass
        self.me = AGENT_NONE
        self.vote_candidate = AGENT_NONE
        self.game_info = None  # type: ignore
        self.comingout_map = {}
        self.divination_reports = []
        self.identification_reports = []
        self.talk_list_head = 0
        self.must_white = []

    def is_alive(self, agent: Agent) -> bool:
        """Return whether the agent is alive.

        Args:
            agent: The agent.

        Returns:
            True if the agent is alive, otherwise false.
        """
        return self.game_info.status_map[agent] == Status.ALIVE

    def get_others(self, agent_list: List[Agent]) -> List[Agent]:
        """Return a list of agents excluding myself from the given list of agents.

        Args:
            agent_list: The list of agent.

        Returns:
            A list of agents excluding myself from agent_list.
        """
        return [a for a in agent_list if a != self.me]

    def get_alive(self, agent_list: List[Agent]) -> List[Agent]:
        """Return a list of alive agents contained in the given list of agents.

        Args:
            agent_list: The list of agents.

        Returns:
            A list of alive agents contained in agent_list.
        """
        return [a for a in agent_list if self.is_alive(a)]

    def get_alive_others(self, agent_list: List[Agent]) -> List[Agent]:
        """Return a list of alive agents that is contained in the given list of agents
        and is not equal to myself.

        Args:
            agent_list: The list of agents.

        Returns:
            A list of alie agents that is contained in agent_list
            and is not equal to myself.
        """
        return self.get_alive(self.get_others(agent_list))

    def random_select(self, agent_list: List[Agent]) -> Agent:
        """Return one agent randomly chosen from the given list of agents.

        Args:
            agent_list: The list of agents.

        Returns:
            A agent randomly chosen from agent_list.
        """
        return random.choice(agent_list) if agent_list else AGENT_NONE

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        self.game_info = game_info
        self.game_setting = game_setting
        self.me = game_info.me
        # Clear fields not to bring in information from the last game.
        self.comingout_map.clear()
        self.divination_reports.clear()
        self.identification_reports.clear()

    def day_start(self) -> None:
        self.talk_list_head = 0
        self.vote_candidate = AGENT_NONE

    def update(self, game_info: GameInfo) -> None: #話す直前に呼ばれる
        self.game_info = game_info  # Update game information.
        for i in range(
            self.talk_list_head, len(game_info.talk_list)
        ):  # Analyze talks that have not been analyzed yet.
            tk: Talk = game_info.talk_list[i]  # The talk to be analyzed.
            talker: Agent = tk.agent
            if talker == self.me:  # Skip my talk.
                continue
            content: Content = Content.compile(tk.text)
            if content.topic == Topic.COMINGOUT:
                self.comingout_map[talker] = content.role
            elif content.topic == Topic.DIVINED:
                self.divination_reports.append(
                    Judge(talker, game_info.day, content.target, content.result)
                )
            elif content.topic == Topic.IDENTIFIED:
                self.identification_reports.append(
                    Judge(talker, game_info.day, content.target, content.result)
                )
            self._get_mustwhite()
        self.talk_list_head = len(game_info.talk_list)  # All done.

    def talk(self) -> Content:
        # Choose an agent to be voted for while talking.
        #
        # The list of fake seers that reported me as a werewolf.
        fake_seers: List[Agent] = [
            j.agent
            for j in self.divination_reports
            if j.target == self.me and j.result == Species.WEREWOLF
        ]
        # Vote for one of the alive agents that were judged as werewolves by non-fake seers.
        reported_wolves: List[Agent] = [
            j.target
            for j in self.divination_reports
            if j.agent not in fake_seers and j.result == Species.WEREWOLF
        ]
        candidates: List[Agent] = self.get_alive_others(reported_wolves)
        # Vote for one of the alive fake seers if there are no candidates.
        if not candidates:
            candidates = self.get_alive(fake_seers)
        # Vote for one of the alive agents if there are no candidates.
        if not candidates:
            candidates = self.get_alive_others(self.game_info.agent_list)
        # Declare which to vote for if not declare yet or the candidate is changed.
        if self.vote_candidate == AGENT_NONE or self.vote_candidate not in candidates:
            self.vote_candidate = self.random_select(candidates)
            if self.vote_candidate != AGENT_NONE:
                return Content(VoteContentBuilder(self.vote_candidate))
        return CONTENT_SKIP

    def vote(self) -> Agent:
        return self.vote_candidate if self.vote_candidate != AGENT_NONE else self.me

    def attack(self) -> Agent:
        raise NotImplementedError()

    def divine(self) -> Agent:
        raise NotImplementedError()

    def guard(self) -> Agent:
        raise NotImplementedError()

    def whisper(self) -> Content:
        raise NotImplementedError()

    def finish(self) -> None:
        pass

    def _get_mustwhite(self) -> List[Agent]:
        """Create a list of confirmed 'white' agents (innocent) based on divination results
        and ensure to include agents confirmed by all Seers."""
        white: List[Agent] = []

        # Count the number of COs for Seer
        seer_candidates = [
            agent for agent, role in self.comingout_map.items() if role == Role.SEER
        ]

        # Create a dictionary to count the number of white confirmations for each agent
        white_confirmations = {}

        # If there are Seers, check their divination results
        for seer in seer_candidates:
            for report in self.divination_reports:
                if report.agent == seer and report.result == Species.HUMAN:
                    # Count confirmations for the target
                    white_confirmations[report.target] = white_confirmations.get(report.target, 0) + 1

        # Add to white list if confirmed by all Seers
        if seer_candidates:  # If there are any Seers
            for target, count in white_confirmations.items():
                if count == len(seer_candidates):  # Confirmed by all Seers
                    white.append(target)

        # If there is exactly one Seer, they are automatically white
        if len(seer_candidates) == 1:
            white.append(seer_candidates[0])

        # Count the number of COs for Medium
        medium_candidates = [
            agent for agent, role in self.comingout_map.items() if role == Role.MEDIUM
        ]

        # If there is exactly one Medium, they are automatically white
        if len(medium_candidates) == 1:
            white.append(medium_candidates[0])

        # Remove duplicates and return the list of confirmed white agents
        self.must_white = list(set(white))

        # Log the confirmed white agents
        try:
            with open("../aiwolf24/playground/log.txt", "a") as file:
                if self.must_white:
                    file.write(f"Confirmed white agents: {self.must_white[:]}\n")
                else:
                    file.write("NO_WHITE.")
        except Exception as e:
            print(f"Error writing to log file: {e}")

        return self.must_white
