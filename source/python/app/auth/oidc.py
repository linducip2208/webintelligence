"""Enterprise identity abstraction: local + OIDC/OAuth2 provider interface.

Local login stays fully functional. OIDC is configuration-driven:
without OIDC_ISSUER/CLIENT_ID the provider reports honestly
`configured: false` and login attempts return 501 — never fake SSO.
"""
import json
import os
import urllib.parse
import urllib.request


class AuthProvider:
    name = "local"

    def status(self):
        return {"name": self.name, "configured": True}

    def login_url(self, redirect_uri: str, state: str):
        raise NotImplementedError


class LocalProvider(AuthProvider):
    name = "local"


class OIDCProvider(AuthProvider):
    name = "oidc"

    def __init__(self, issuer="", client_id="", client_secret=""):
        self.issuer = (issuer or "").rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._doc = None

    @property
    def configured(self):
        return bool(self.issuer and self.client_id)

    def status(self):
        return {"name": self.name, "configured": self.configured,
                "issuer": self.issuer or ""}

    def discovery(self, timeout=15):
        if not self.issuer:
            raise RuntimeError("oidc not configured (OIDC_ISSUER)")
        if self._doc is None:
            with urllib.request.urlopen(self.issuer + "/.well-known/openid-configuration",
                                        timeout=timeout) as r:
                self._doc = json.loads(r.read().decode())
        for k in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            if k not in self._doc:
                raise RuntimeError(f"oidc discovery missing {k}")
        return self._doc

    def login_url(self, redirect_uri: str, state: str):
        doc = self.discovery()
        q = urllib.parse.urlencode({"client_id": self.client_id,
                                    "redirect_uri": redirect_uri,
                                    "response_type": "code", "scope": "openid email profile",
                                    "state": state})
        return doc["authorization_endpoint"] + "?" + q


def from_env(get=os.getenv):
    return {"local": LocalProvider(),
            "oidc": OIDCProvider(get("OIDC_ISSUER", ""), get("OIDC_CLIENT_ID", ""),
                                 get("OIDC_CLIENT_SECRET", ""))}
