import jwt
import logging
import os

logger = logging.getLogger(__name__)

def decrypt_jwt(encrypted_token, keyofInterest):
    # String with "Bearer <token>".  Strip out "Bearer"...
    prefix = 'Bearer'
    if not encrypted_token.startswith(prefix):
        error_message = f'\"Bearer\" not found in token: {encrypted_token}'
        logger.error(error_message)
        raise Exception(error_message)

    stripped_token = encrypted_token[len(prefix):].strip()
    algorithms = ["HS256"]  # using the default, if it is changed then it should also be changed in the frontend code
#   authentication_key = os.getenv("JWT_KEY")
    decoded_jwt = jwt.api_jwt.decode(stripped_token, options={"verify_signature": False})

    logger.debug(f"decoded_jwt: {decoded_jwt}")

    # We might have a nested key in JWT (dict within dict).  In that case, flatKey will express the hierarchy and so we
    # will iteratively chunk through it.
    decoded_key = 'MISSING KEY ' + keyofInterest
    for s in keyofInterest.split('.'):
        if s in decoded_jwt:
            decoded_jwt = decoded_jwt[s]
            decoded_key = decoded_jwt
            if (type(decoded_jwt) is dict):
                continue
            else:
                if type(decoded_key) is list:
                    decoded_key = decoded_key[0]
                return decoded_key
    return decoded_key
