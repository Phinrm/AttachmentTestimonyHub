from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


class CompanyEmailTokenGenerator(PasswordResetTokenGenerator):
    pass


company_email_token = CompanyEmailTokenGenerator()


def encode_uid(pk):
    return urlsafe_base64_encode(force_bytes(pk))


def decode_uid(uidb64):
    return force_str(urlsafe_base64_decode(uidb64))
