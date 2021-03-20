"""
Helper functions for working with the csh_ldap library
"""

from functools import lru_cache
from datetime import date

from csh_ldap import CSHLDAP

from packet import app


class MockMember:

    def __init__(self, uid: str, groups: list = None, cn: str = None, room_number: int = None):
        self.uid = uid
        self.groups = groups if groups else list()
        if room_number:
            self.room_number = room_number
        self.cn = cn if cn else uid.title() # pylint: disable=invalid-name


    def __eq__(self, other):
        if type(other) is type(self):
            return self.uid == other.uid
        return False


    def __hash__(self):
        return hash(self.uid)


    def __repr__(self):
        return f'MockMember(uid: {self.uid}, groups: {self.groups})'


class LDAPWrapper:

    def __init__(self, cshldap=None, mock_members=None):
        self.ldap = cshldap
        self.mock_members = mock_members
        if self.ldap:
            app.logger.info('LDAP configured with CSH LDAP')
        else:
            app.logger.info('LDAP configured with local mock')


    def _get_group_members(self, group):
        """
        :return: A list of CSHMember instances
        """
        if self.ldap:
            return self.ldap.get_group(group).get_members()
        else:
            return list(filter(lambda member: group in member.groups, self.mock_members))


    def _is_member_of_group(self, member, group):
        """
        :param member: A CSHMember instance
        """
        if self.ldap:
            for group_dn in member.get('memberOf'):
                if group == group_dn.split(',')[0][3:]:
                    return True
            return False
        else:
            return group in member.groups

    def get_groups(self, member):
        if self.ldap:
            return list(
                    map(
                        lambda g: g[0][3:],
                        filter(
                            lambda d: d[1] == 'cn=groups',
                            map(
                                lambda group_dn: group_dn.split(','),
                                member.get('memberOf')
                                )
                            )
                        )
                    )
        else:
            return member.groups



    # Getters

    @lru_cache(maxsize=256)
    def get_member(self, username):
        """
        :return: A CSHMember instance
        """
        if self.ldap:
            return self.ldap.get_member(username, uid=True)
        else:
            member = next(filter(lambda member: member.uid == username, self.mock_members), None)
            if member:
                return member
            raise KeyError('Invalid Search Name')


    def get_active_members(self):
        """
        Gets all current, dues-paying members
        :return: A list of CSHMember instances
        """
        return self._get_group_members('active')


    def get_intro_members(self):
        """
        Gets all freshmen members
        :return: A list of CSHMember instances
        """
        return self._get_group_members('intromembers')


    def get_eboard(self):
        """
        Gets all voting members of eboard
        :return: A list of CSHMember instances
        """
        members = self._get_group_members('eboard-chairman') + self._get_group_members('eboard-evaluations'
            ) + self._get_group_members('eboard-financial') + self._get_group_members('eboard-history'
            ) + self._get_group_members('eboard-imps') + self._get_group_members('eboard-opcomm'
            ) + self._get_group_members('eboard-research') + self._get_group_members('eboard-social'
            )

        return members


    def get_live_onfloor(self):
        """
        All upperclassmen who live on floor and are not eboard
        :return: A list of CSHMember instances
        """
        members = []
        onfloor = self._get_group_members('onfloor')
        for member in onfloor:
            if self.get_roomnumber(member) and not self.is_eboard(member):
                members.append(member)

        return members


    def get_active_rtps(self):
        """
        All active RTPs
        :return: A list of CSHMember instances
        """
        return [member.uid for member in self._get_group_members('active_rtp')]


    def get_3das(self):
        """
        All 3das
        :return: A list of CSHMember instances
        """
        return [member.uid for member in self._get_group_members('3da')]


    def get_webmasters(self):
        """
        All webmasters
        :return: A list of CSHMember instances
        """
        return [member.uid for member in self._get_group_members('webmaster')]


    def get_constitutional_maintainers(self):
        """
        All constitutional maintainers
        :return: A list of CSHMember instances
        """
        return [member.uid for member in self._get_group_members('constitutional_maintainers')]

    def get_wiki_maintainers(self):
        """
        All wiki maintainers
        :return: A list of CSHMember instances
        """
        return [member.uid for member in self._get_group_members('wiki_maintainers')]


    def get_drink_admins(self):
        """
        All drink admins
        :return: A list of CSHMember instances
        """
        return [member.uid for member in self._get_group_members('drink')]


    def get_eboard_role(self, member):
        """
        :param member: A CSHMember instance
        :return: A String or None
        """

        return_val = None

        if self._is_member_of_group(member, 'eboard-chairman'):
            return_val = 'Chairperson'
        elif self._is_member_of_group(member, 'eboard-evaluations'):
            return_val = 'Evals'
        elif self._is_member_of_group(member, 'eboard-financial'):
            return_val = 'Financial'
        elif self._is_member_of_group(member, 'eboard-history'):
            return_val = 'History'
        elif self._is_member_of_group(member, 'eboard-imps'):
            return_val = 'Imps'
        elif self._is_member_of_group(member, 'eboard-opcomm'):
            return_val = 'OpComm'
        elif self._is_member_of_group(member, 'eboard-research'):
            return_val = 'R&D'
        elif self._is_member_of_group(member, 'eboard-social'):
            return_val = 'Social'
        elif self._is_member_of_group(member, 'eboard-secretary'):
            return_val = 'Secretary'

        return return_val


    # Status checkers
    def is_eboard(self, member):
        """
        :param member: A CSHMember instance
        """
        return self._is_member_of_group(member, 'eboard')


    def is_evals(self, member):
        return self._is_member_of_group(member, 'eboard-evaluations')


    def is_rtp(self, member):
        return self._is_member_of_group(member, 'rtp')


    def is_intromember(self, member):
        """
        :param member: A CSHMember instance
        """
        return self._is_member_of_group(member, 'intromembers')


    def is_on_coop(self, member):
        """
        :param member: A CSHMember instance
        """
        if date.today().month > 6:
            return self._is_member_of_group(member, 'fall_coop')
        else:
            return self._is_member_of_group(member, 'spring_coop')


    def get_roomnumber(self, member): # pylint: disable=no-self-use
        """
        :param member: A CSHMember instance
        """
        try:
            return member.roomNumber
        except AttributeError:
            return None


if app.config['LDAP_BIND_DN'] and app.config['LDAP_BIND_PASS']:
    ldap = LDAPWrapper(cshldap=CSHLDAP(app.config['LDAP_BIND_DN'],
                                     app.config['LDAP_BIND_PASS']
                                    )
)
else:
    ldap = LDAPWrapper(
            mock_members=list(
                map(
                    lambda mock_dict: MockMember(**mock_dict),
                    app.config['LDAP_MOCK_MEMBERS']
                   )
                )
            )
