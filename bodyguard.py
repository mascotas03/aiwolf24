#
# bodyguard.py
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

from typing import List

from aiwolf import Agent, GameInfo, GameSetting, Role, Species
from aiwolf.constant import AGENT_NONE

from villager import SampleVillager


class SampleBodyguard(SampleVillager):
    """Sample bodyguard agent."""

    to_be_guarded: Agent
    """Target of guard."""

    def __init__(self) -> None:
        """Initialize a new instance of SampleBodyguard."""
        super().__init__()
        self.to_be_guarded = AGENT_NONE

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """Initialize game information."""
        super().initialize(game_info, game_setting)
        self.to_be_guarded = AGENT_NONE

    def guard(self) -> Agent:
        """Determine whom to guard."""
        # Guard one of the alive non-fake seers.
        candidates: List[Agent] = self.get_alive(
            [
                j.agent
                for j in self.divination_reports
                if j.result != Species.WEREWOLF or j.target != self.me
            ]
        )
        # Guard one of the alive mediums if there are no candidates.
        if not candidates:
            candidates = [
                a
                for a in self.comingout_map
                if self.is_alive(a) and self.comingout_map[a] == Role.MEDIUM
            ]
        # Guard one of the alive agents if there are no candidates.
        if not candidates:
            candidates = self.get_alive_others(self.game_info.agent_list)
        # Update a guard candidate if the candidate is changed.
        if self.to_be_guarded == AGENT_NONE or self.to_be_guarded not in candidates:
            self.to_be_guarded = self.random_select(candidates)
        return self.to_be_guarded if self.to_be_guarded != AGENT_NONE else self.me

    def update(self, game_info: GameInfo) -> None:
        """Update game information based on new talks."""
        super().update(game_info)  # Call the parent class's update method
        for talk in game_info.talk_list:
            content: Content = Content.compile(talk.text)
            if content.topic == Topic.COMINGOUT:
                self.comingout_map[talk.agent] = content.role

    def mustwhite(self) -> List[Agent]:
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
                    if report.target in white_confirmations:
                        white_confirmations[report.target] += 1
                    else:
                        white_confirmations[report.target] = 1

        # Add to white list if confirmed by all Seers
        if seer_candidates:  # If there are any Seers
            for target, count in white_confirmations.items():
                if count == len(seer_candidates):  # Confirmed by all Seers
                    white.append(target)

        # Count the number of COs for Medium
        medium_candidates = [
            agent for agent, role in self.comingout_map.items() if role == Role.MEDIUM
        ]

        # If there is exactly one Medium, they are automatically white
        if len(medium_candidates) == 1:
            medium = medium_candidates[0]
            white.append(medium)

        # Remove duplicates and return the list of confirmed white agents
        return list(set(white))
