
from pydantic import BaseModel
from uuid import UUID


class ThirdPartyOauthDataResponse(BaseModel):
    clientId: str
    redirectUri: str
    codeChallenge: str
    state: str
    scopes: str
    codeChallengeMethod: str
    responseType: str
    oauthConnectUrl: str

class ThirdPartyOauthResponse(BaseModel):
    status_code: int
    success: bool
    access_token: str
    refresh_token: str
    expires_in: int
    message: str