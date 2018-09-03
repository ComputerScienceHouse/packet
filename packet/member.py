from .models import Freshman, FreshSignature, UpperSignature, MiscSignature


def signed_packets(member):
    
    # Checks to see if member is a freshman 
    if Freshman.query.filter_by(rit_username=member).first() is not None:
        return FreshSignature.query.filter_by(freshman_username=member, signed=True).all()
    
    # Checks to see if member is an upper_classmen
    if UpperSignature.query.filter_by(member=member).first() is not None:
        return UpperSignature.query.filter_by(member=member, signed=True).all()
    return MiscSignature.query.filter_by(member=member).all()
