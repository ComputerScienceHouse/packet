"""
Helper functions for working with the csh_ldap library
"""

from functools import lru_cache
from datetime import date
from typing import Optional, cast, Any, Union

from csh_ldap import CSHLDAP, CSHMember

from packet import app


class MockMember:
    def __init__(
        self,
        uid: str,
        groups: Optional[list] = None,
        cn: Optional[str] = None,
        room_number: Optional[int] = None,
    ):
        """
        MockMember constructor

        Args:
            uid: The unique identifier for the member.
            groups: A list of groups the member belongs to.
            cn: The common name of the member.
            room_number: The room number of the member.
        """

        self.uid: str = uid
        self.groups: list[str] = groups if groups else list()

        self.room_number: Optional[int] = room_number if room_number else None

        self.cn: str = cn if cn else uid.title()

    def __eq__(self, other: Any) -> bool:
        """
        Check equality between two MockMember instances.

        Args:
            other: The other MockMember instance to compare against.

        Returns:
            True if the instances are equal, False otherwise.
        """

        if type(other) is type(self):
            return self.uid == other.uid

        return False

    def __hash__(self) -> int:
        """
        Returns the hash of the MockMember instance.

        Returns:
            The hash of the MockMember instance.
        """

        return hash(self.uid)

    def __repr__(self) -> str:
        """
        Returns a string representation of the MockMember instance.

        Returns:
            A string representation of the MockMember instance.
        """

        return f"MockMember(uid: {self.uid}, groups: {self.groups})"


class LDAPWrapper:
    def __init__(
        self,
        cshldap: Optional[CSHLDAP] = None,
        mock_members: Optional[list[MockMember]] = None,
    ):
        """
        Initialize the LDAPWrapper.

        Args:
            cshldap: An instance of the CSHLDAP class.
            mock_members: A list of MockMember instances.
        """

        self.ldap = cshldap
        self.mock_members = cast(list[MockMember], mock_members)

        if self.ldap:
            app.logger.info("LDAP configured with CSH LDAP")
        else:
            app.logger.info("LDAP configured with local mock")

    def _get_group_members(self, group: str) -> list[CSHMember]:
        """
        Get members of a specific group.

        Args:
            group: The name of the group to retrieve members from.

        Returns:
            A list of CSHMember instances belonging to the specified group.
        """

        if self.ldap:
            return self.ldap.get_group(group).get_members()

        return list(filter(lambda member: group in member.groups, self.mock_members))

    def _is_member_of_group(self, member: CSHMember, group: str) -> bool:
        """
        Check if a member is part of a specific group.

        Args:
            member: A CSHMember instance.
            group: The name of the group to check membership against.

        Returns:
            True if the member is part of the group, False otherwise.
        """

        if not self.ldap:
            return group in member.groups

        for group_dn in member.get("memberOf"):
            if group == group_dn.split(",")[0][3:]:
                return True

        return False

    def get_groups(self, member: CSHMember) -> list[str]:
        """
        Get all groups the member is part of.

        Args:
            member: A CSHMember instance.

        Returns:
            A list of group names the member belongs to.
        """

        if not self.ldap:
            return member.groups

        return list(
            map(
                lambda g: g[0][3:],
                filter(
                    lambda d: d[1] == "cn=groups",
                    map(lambda group_dn: group_dn.split(","), member.get("memberOf")),
                ),
            )
        )

    # Getters

    @lru_cache(maxsize=256)
    def get_member(self, username: str) -> CSHMember:
        """
        Get a member by their username.

        Returns:
            A CSHMember instance.
        """

        if self.ldap:
            return self.ldap.get_member(username, uid=True)

        member = next(
            filter(lambda member: member.uid == username, self.mock_members), None
        )

        if not member:
            raise KeyError("Invalid Search Name")

        return member

    def get_active_members(self) -> list[CSHMember]:
        """
        Gets all current, dues-paying members

        Returns:
            A list of CSHMember instances.
        """

        return self._get_group_members("active")

    def get_intro_members(self) -> list[CSHMember]:
        """
        Gets all freshmen members

        Returns:
            A list of CSHMember instances.
        """

        return self._get_group_members("intromembers")

    def get_eboard(self) -> list[CSHMember]:
        """
        Gets all voting members of eboard

        Returns:
            A list of CSHMember instances.
        """

        groups: tuple[str, ...] = (
            "eboard-chairman",
            "eboard-evaluations",
            "eboard-financial",
            "eboard-history",
            "eboard-imps",
            "eboard-opcomm",
            "eboard-research",
            "eboard-social",
            "eboard-pr",
        )

        members: list[CSHMember] = []

        for group in groups:
            members.extend(self._get_group_members(group))

        return members

    def get_live_onfloor(self) -> list[CSHMember]:
        """
        All upperclassmen who live on floor and are not eboard

        Returns:
            A list of CSHMember instances.
        """

        members: list[CSHMember] = []

        onfloor: list[CSHMember] = self._get_group_members("onfloor")

        for member in onfloor:
            if self.get_roomnumber(member) and not self.is_eboard(member):
                members.append(member)

        return members

    def get_active_rtps(self) -> list[CSHMember]:
        """
        All active RTPs

        Returns:
            A list of CSHMember instances.
        """

        return [member.uid for member in self._get_group_members("active_rtp")]

    def get_3das(self) -> list[CSHMember]:
        """
        All 3das

        Returns:
            A list of CSHMember instances.
        """

        return [member.uid for member in self._get_group_members("3da")]

    def get_webmasters(self) -> list[CSHMember]:
        """
        All webmasters

        Returns:
            A list of CSHMember instances.
        """

        return [member.uid for member in self._get_group_members("webmaster")]

    def get_constitutional_maintainers(self) -> list[CSHMember]:
        """
        All constitutional maintainers

        Returns:
            A list of CSHMember instances.
        """

        return [
            member.uid
            for member in self._get_group_members("constitutional_maintainers")
        ]

    def get_wiki_maintainers(self) -> list[CSHMember]:
        """
        All wiki maintainers

        Returns:
            A list of CSHMember instances.
        """

        return [member.uid for member in self._get_group_members("wiki_maintainers")]

    def get_drink_admins(self) -> list[CSHMember]:
        """
        All drink admins

        Returns:
            A list of CSHMember instances.
        """

        return [member.uid for member in self._get_group_members("drink")]

    def get_eboard_role(self, member: CSHMember) -> Optional[str]:
        """
        Get the eboard role of a member.

        Args:
            member (CSHMember): The member to check.

        Returns:
            Optional[str]: The eboard role of the member, or None if not found.
        """

        groups: dict[str, str] = {
            "eboard-chairman": "Chairperson",
            "eboard-evaluations": "Evals",
            "eboard-financial": "Financial",
            "eboard-history": "History",
            "eboard-imps": "Imps",
            "eboard-opcomm": "OpComm",
            "eboard-research": "R&D",
            "eboard-social": "Social",
            "eboard-pr": "PR",
            "eboard-secretary": "Secretary",
        }

        for group, role in groups.items():
            if self._is_member_of_group(member, group):
                return role

        return None

    # Status checkers
    def is_eboard(self, member: CSHMember) -> bool:
        """
        Check if a member is part of the eboard.

        Args:
            member (CSHMember): The member to check.

        Returns:
            bool: True if the member is part of the eboard, False otherwise.
        """

        return self._is_member_of_group(member, "eboard")

    def is_evals(self, member: CSHMember) -> bool:
        """
        Check if a member is part of the evaluations team.

        Args:
            member (CSHMember): The member to check.

        Returns:
            bool: True if the member is part of the evaluations team, False otherwise.
        """

        return self._is_member_of_group(member, "eboard-evaluations")

    def is_rtp(self, member: CSHMember) -> bool:
        """
        Check if a member is part of the RTP team.

        Args:
            member (CSHMember): The member to check.

        Returns:
            bool: True if the member is part of the RTP team, False otherwise.
        """

        return self._is_member_of_group(member, "rtp")

    def is_intromember(self, member: CSHMember) -> bool:
        """
        Check if a member is a freshman.

        Args:
            member (CSHMember): The member to check.

        Returns:
            bool: True if the member is a freshman, False otherwise.
        """

        return self._is_member_of_group(member, "intromembers")

    def is_on_coop(self, member: CSHMember) -> bool:
        """
        Check if a member is on a co-op.

        Args:
            member (CSHMember): The member to check.

        Returns:
            bool: True if the member is on a co-op, False otherwise.
        """

        if date.today().month > 6:
            return self._is_member_of_group(member, "fall_coop")

        return self._is_member_of_group(member, "spring_coop")

    def get_roomnumber(self, member: CSHMember) -> Optional[int]:
        """
        Get the room number of a member.

        Args:
            member (CSHMember): The member to check.

        Returns:
            Optional[int]: The room number of the member, or None if not found.
        """

        try:
            return member.roomNumber
        except AttributeError:
            return None


ldap: LDAPWrapper = LDAPWrapper(
    mock_members=list(
        map(
            lambda mock_dict: MockMember(**mock_dict),
            app.config["LDAP_MOCK_MEMBERS"],
        )
    )
)

if app.config["LDAP_BIND_DN"] and app.config["LDAP_BIND_PASS"]:
    ldap = LDAPWrapper(
        cshldap=CSHLDAP(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PASS"])
    )
