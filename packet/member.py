from .models import Freshman, FreshSignature, UpperSignature, MiscSignature


def signed_packets(member):
    is_freshman = Freshman.query.filter_by(rit_username=member).first() is not None
    if is_freshman:
        return FreshSignature.query.filter_by(freshman_username=member, signed=True)
    is_upper = UpperSignature.query.filter_by(member=member).first() is not None
    if is_upper:
        return UpperSignature.query.filter_by(member=member, signed=True)
    return MiscSignature.query.filter_by(member=member)
