import hashlib

from functools import lru_cache

import urllib.request

from flask import redirect

import ldap

from packet import _ldap


def _ldap_get_group_members(group):
    return _ldap.get_group(group).get_members()


def _ldap_is_member_of_group(member, group):
    group_list = member.get("memberOf")
    for group_dn in group_list:
        if group == group_dn.split(",")[0][3:]:
            return True
    return False


def _ldap_add_member_to_group(account, group):
    if not _ldap_is_member_of_group(account, group):
        _ldap.get_group(group).add_member(account, dn=False)


def _ldap_remove_member_from_group(account, group):
    if _ldap_is_member_of_group(account, group):
        _ldap.get_group(group).del_member(account, dn=False)


@lru_cache(maxsize=1024)
def _ldap_is_member_of_directorship(account, directorship):
    directors = _ldap.get_directorship_heads(directorship)
    for director in directors:
        if director.uid == account.uid:
            return True
    return False


# Getters


def ldap_get_member(username):
    return _ldap.get_member(username, uid=True)


@lru_cache(maxsize=1024)
def ldap_get_active_members():
    return _ldap_get_group_members("active")


@lru_cache(maxsize=1024)
def ldap_get_intro_members():
    return _ldap_get_group_members("intromembers")


@lru_cache(maxsize=1024)
def ldap_get_onfloor_members():
    return _ldap_get_group_members("onfloor")


@lru_cache(maxsize=1024)
def ldap_get_current_students():
    return _ldap_get_group_members("current_student")


@lru_cache(maxsize=1024)
def ldap_get_all_members():
    return _ldap_get_group_members("member")


@lru_cache(maxsize=1024)
def ldap_get_groups(account):
    group_list = account.get("memberOf")
    groups = []
    for group_dn in group_list:
        if "cn=groups,cn=accounts" in group_dn:
            groups.append(group_dn.split(",")[0][3:])
    return groups


@lru_cache(maxsize=1024)
def ldap_get_group_desc(group):
    con = _ldap.get_con()
    results = con.search_s(
        "cn=groups,cn=accounts,dc=csh,dc=rit,dc=edu",
        ldap.SCOPE_SUBTREE,
        "(cn=%s)" % group,
        ['description'])
    return results[0][1]['description'][0].decode('utf-8')


@lru_cache(maxsize=1024)
def ldap_get_eboard():
    members = _ldap_get_group_members("eboard-chairman") + _ldap_get_group_members("eboard-evaluations"
        ) + _ldap_get_group_members("eboard-financial") + _ldap_get_group_members("eboard-history"
        ) + _ldap_get_group_members("eboard-imps") + _ldap_get_group_members("eboard-opcomm"
        ) + _ldap_get_group_members("eboard-research") + _ldap_get_group_members("eboard-social"
        ) + _ldap_get_group_members("eboard-secretary")

    return members


# Status checkers

def ldap_is_active(account):
    return _ldap_is_member_of_group(account, 'active')


def ldap_is_alumni(account):
    # If the user is not active, they are an alumni.
    return not _ldap_is_member_of_group(account, 'active')


def ldap_is_eboard(account):
    return _ldap_is_member_of_group(account, 'eboard')


def ldap_is_rtp(account):
    return _ldap_is_member_of_group(account, 'rtp')


def ldap_is_intromember(account):
    return _ldap_is_member_of_group(account, 'intromembers')


def ldap_is_onfloor(account):
    return _ldap_is_member_of_group(account, 'onfloor')


def ldap_is_current_student(account):
    return _ldap_is_member_of_group(account, 'current_student')


# Directorships

def ldap_is_financial_director(account):
    return _ldap_is_member_of_directorship(account, 'financial')


def ldap_is_eval_director(account):
    return _ldap_is_member_of_directorship(account, 'evaluations')


def ldap_is_chairman(account):
    return _ldap_is_member_of_directorship(account, 'chairman')


def ldap_is_history(account):
    return _ldap_is_member_of_directorship(account, 'history')


def ldap_is_imps(account):
    return _ldap_is_member_of_directorship(account, 'imps')


def ldap_is_social(account):
    return _ldap_is_member_of_directorship(account, 'Social')


def ldap_is_rd(account):
    return _ldap_is_member_of_directorship(account, 'research')


# Setters

def ldap_set_housingpoints(account, housing_points):
    account.housingPoints = housing_points
    ldap_get_current_students.cache_clear()
    ldap_get_member.cache_clear()


def ldap_set_roomnumber(account, room_number):
    if room_number == "":
        room_number = None
    account.roomNumber = room_number
    ldap_get_current_students.cache_clear()
    ldap_get_member.cache_clear()


def ldap_set_active(account):
    _ldap_add_member_to_group(account, 'active')
    ldap_get_active_members.cache_clear()
    ldap_get_member.cache_clear()


def ldap_set_inactive(account):
    _ldap_remove_member_from_group(account, 'active')
    ldap_get_active_members.cache_clear()
    ldap_get_member.cache_clear()


def ldap_set_current_student(account):
    _ldap_add_member_to_group(account, 'current_student')
    ldap_get_current_students.cache_clear()
    ldap_get_member.cache_clear()


def ldap_set_non_current_student(account):
    _ldap_remove_member_from_group(account, 'current_student')
    ldap_get_current_students.cache_clear()
    ldap_get_member.cache_clear()

def ldap_multi_update(uid, attribute, value):
    dn = "uid={},cn=users,cn=accounts,dc=csh,dc=rit,dc=edu".format(
        uid
    )

    try:
        current = _ldap.get_member(uid, uid=True).get(attribute)
    except KeyError:
        current = []

    remove = list(set(current) - set(value))
    add = list(set(value) - set(current))

    conn = _ldap.get_con()
    mod_list = []

    for entry in remove:
        mod = (ldap.MOD_DELETE, attribute, entry.encode('utf-8'))
        mod_list.append(mod)

    for entry in add:
        if entry:
            mod = (ldap.MOD_ADD, attribute, entry.encode('utf-8'))
            mod_list.append(mod)

    conn.modify_s(dn, mod_list)


# pylint: disable=too-many-branches
def ldap_update_profile(form_input, uid):
    account = _ldap.get_member(uid, uid=True)
    empty = ["None", ""]
    for key, value in form_input.items():
        if value in empty:
            form_input[key] = None

    if not form_input["name"] == account.cn:
        account.cn = form_input["name"]

    if not form_input["birthday"] == account.birthday:
        account.birthday = form_input["birthday"]

    try:
        if not form_input["phone"] == account.get("mobile"):
            ldap_multi_update(uid, "mobile", form_input["phone"])
    except KeyError:
        ldap_multi_update(uid, "mobile", form_input["phone"])


    if not form_input["plex"] == account.plex:
        account.plex = form_input["plex"]

    if "major" in form_input.keys():
        if not form_input["major"] == account.major:
            account.major = form_input["major"]

    if "minor" in form_input.keys():
        if not form_input["minor"] == account.minor:
            account.minor = form_input["minor"]

    if "ritYear" in form_input.keys():
        if not form_input["ritYear"] == account.ritYear:
            account.ritYear = form_input["ritYear"]

    if not form_input["website"] == account.homepageURL:
        account.homepageURL = form_input["website"]

    if not form_input["github"] == account.github:
        account.github = form_input["github"]

    if not form_input["twitter"] == account.twitterName:
        account.twitterName = form_input["twitter"]

    if not form_input["blog"] == account.blogURL:
        account.blogURL = form_input["blog"]

    if not form_input["resume"] == account.resumeURL:
        account.resumeURL = form_input["resume"]

    if not form_input["google"] == account.googleScreenName:
        account.googleScreenName = form_input["google"]

    try:
        if not form_input["mail"] == account.mail:
            ldap_multi_update(uid, "mail", form_input["mail"])
    except KeyError:
        ldap_multi_update(uid, "mail", form_input["mail"])

    try:
        if not form_input["nickname"] == account.nickname:
            ldap_multi_update(uid, "nickname", form_input["nickname"])
    except KeyError:
        ldap_multi_update(uid, "nickname", form_input["nickname"])

    if not form_input["shell"] == account.shell:
        account.loginShell = form_input["shell"]


def ldap_get_roomnumber(account):
    try:
        return account.roomNumber
    except AttributeError:
        return ""


@lru_cache(maxsize=1024)
def ldap_search_members(query):
    con = _ldap.get_con()
    filt = str("(|(description=*{0}*)"
                    "(displayName=*{0}*)"
                    "(mail=*{0}*)"
                    "(nickName=*{0}*)"
                    "(plex=*{0}*)"
                    "(sn=*{0}*)"
                    "(uid=*{0}*)"
                    "(mobile=*{0}*)"
                    "(twitterName=*{0}*)"
                    "(github=*{0}*))").format(query)

    res = con.search_s(
        "dc=csh,dc=rit,dc=edu",
        ldap.SCOPE_SUBTREE,
        filt,
        ['uid'])

    ret = []

    for uid in res:
        try:
            mem = (str(uid[1]).split('\'')[3])
            ret.append(ldap_get_member(mem))
        except IndexError:
            continue

    return ret


@lru_cache(maxsize=1024)
def ldap_get_year(year):
    con = _ldap.get_con()
    filt = str("(&(memberSince>={}0801010101-0400)(memberSince<={}0801010101-0400))").format(year, str(int(year) + 1))

    res = con.search_s(
        "dc=csh,dc=rit,dc=edu",
        ldap.SCOPE_SUBTREE,
        filt,
        ['uid'])

    ret = []

    for uid in res:
        try:
            mem = (str(uid[1]).split('\'')[3])
            ret.append(ldap_get_member(mem))
        except IndexError:
            continue

    return ret


@lru_cache(maxsize=1024)
def get_image(uid):
    try:
        account = ldap_get_member(uid)
        image = account.jpegPhoto
        github = account.github
        twitter = account.twitterName
    except KeyError:
        return redirect(get_gravatar(), code=302)

    # Return stored Image
    if image:
        return image

    # Get Gravatar
    url = get_gravatar(uid)
    try:
        gravatar = urllib.request.urlopen(url)
        if gravatar.getcode() == 200:
            return redirect(url, code=302)
    except urllib.error.HTTPError:
        pass

    # Get GitHub Photo
    if github:
        url = "https://github.com/" + github + ".png?size=250"
        try:
            urllib.request.urlopen(url)
            return redirect(url, code=302)
        except urllib.error.HTTPError:
            pass

    # Get Twitter Photo
    if twitter:
        url = "https://twitter.com/" + twitter + "/profile_image?size=original"
        try:
            urllib.request.urlopen(url)
            return redirect(url, code=302)
        except urllib.error.HTTPError:
            pass

    # Fall back to default
    return redirect(get_gravatar(), code=302)


@lru_cache(maxsize=1024)
def get_gravatar(uid=None):
    if uid:
        addr = uid + "@csh.rit.edu"
        url = "https://gravatar.com/avatar/" + hashlib.md5(addr.encode('utf8')).hexdigest() +".jpg?d=404&s=250"
    else:
        addr = "null@csh.rit.edu"
        url = "https://gravatar.com/avatar/" + hashlib.md5(addr.encode('utf8')).hexdigest() + ".jpg?d=mm&s=250"
    return url
