# Connectors — Example-Corp

| Name | Provider | Auth | Read scopes | Write scopes (explicit allowlist) | On failure |
|---|---|---|---|---|---|
| crm | (bind your CRM here) | OAuth2 | contacts, orgs, deals, notes | notes.create ONLY | fail loud, notify |
| email | (bind your provider) | OAuth2 | inbox.read | NONE (drafts surfaced to human) | fail loud |
| calendar | (bind your provider) | OAuth2 | events.read | NONE in v0.1 | skip + note |
| linkedin | none (ToS) | n/a | n/a | n/a — deeplink hand-send per Decision 4 | n/a |

Writes are attributed "by AI agent on behalf of <BDOwner>" per decisions.md.
