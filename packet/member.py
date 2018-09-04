from .models import Freshman, FreshSignature, UpperSignature, MiscSignature


def signed_packets(member):
    # Checks whether or not member is a freshman
    if Freshman.query.filter_by(rit_username=member).first() is not None:
        return FreshSignature.query.filter_by(freshman_username=member, signed=True).all()
    # Checks whether or not member is an upperclassman
    if UpperSignature.query.filter_by(member=member).first() is not None:
        return UpperSignature.query.filter_by(member=member, signed=True).all()
    return MiscSignature.query.filter_by(member=member).all()
