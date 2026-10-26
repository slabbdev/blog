---
titre: "Gheist: 13,500 secret-dumping workflows planted with stolen GitHub tokens — audit yours in 5 minutes"
date: 2026-10-26
themes: securite, github
resume: "A campaign called Gheist planted 13,500 secret-dumping workflows with stolen GitHub tokens — base32 defeats log masking, permissions:{} protects nothing, and the exfil channel is GitHub itself. The audit that tells you in 5 minutes if you were hit."
source: https://dev.to/slabb/gheist-13500-secret-dumping-workflows-planted-with-stolen-github-tokens-audit-yours-in-5-minutes-299f
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fztfygwgyki6eaaqty4nq.png
image_alt: "Gheist: 13,500 secret-dumping workflows planted with stolen GitHub tokens — audit yours in 5 minutes"
---

> While everyone watched LiteLLM, a quieter campaign spent five weeks doing something worse: taking stolen GitHub tokens and committing a **secret-dumping workflow into every repository they could reach** — **13,500 planted branches across 850+ compromised accounts**, personal projects and **private enterprise repos** included. Wiz published the full autopsy yesterday. The campaign is called Gheist, it dumps your org secrets, your cloud credentials, and — the line that made me write this — it specifically hunts **AI provider keys: Anthropic, Hugging Face, Groq, NVIDIA**. Your agents' keys, straight out of your CI.

This post is the mechanics and the audit. The whole check runs in five minutes with `gh`, tonight, on your own account and orgs.

## The attack, in four moves

Gheist's tooling takes a stolen token (sourced from infostealer logs and prior supply-chain incidents — the same family that hit Trivy in March), enumerates every repo it can touch, and plants a branch `ci-sync-XXXXXX` containing one workflow, committed as `ci: sync config`, unsigned. The workflow is two dumb lines: dump `env` and `toJSON(secrets)`, **base32-encoded**, print to the workflow log. Then the tool fetches the log through GitHub's API and deletes the run.

Four details make it clever, and all four are worth internalizing:

1. **base32 defeats secret masking.** GitHub masks secret values in logs only when they appear *verbatim*. Encode them and the masking sees nothing. Your `$SECRET` prints safely to the attacker.
2. **`permissions: {}` protects nothing here.** It restricts the auto-generated GITHUB_TOKEN — not the `secrets` context. Half the hardening advice on the internet answers a different attack.
3. **The environment matrix.** Tool B lists the repo's deployment environments, so environment-scoped secrets — usually production, usually the crown jewels — get printed too.
4. **No C2, anywhere.** The secrets exit through GitHub's own API, from GitHub's own IPs, authenticated with a token you issued. There is no attacker domain to block, no exfil host to alert on. The channel is the platform.

On self-hosted runners the payload went further — searching for 31 token formats (private keys, `.env` files, Terraform state, `/proc/*/environ`, Docker sockets, Kubernetes tokens) and AI provider keys specifically. Wiz notes that variant is buggy — wrong runner paths, broken regex, no GCP/Azure collection — which is somehow worse: the campaign is a product under active iteration, shipping features.

## The public/private asymmetry

The single most interesting fact in the autopsy: **public repos were largely saved by one quiet GitHub guardrail**. Since July 28, workflow runs from first-time contributors in public repos sit in `action_required` pending collaborator approval — and every public Gheist run Wiz checked sat there, payload never executed.

That hold **doesn't apply to private repos or GitHub Enterprise Server**. There, the workflows ran, secrets were dumped, and Wiz proved follow-on AWS role assumption from the stolen cloud credentials via CloudTrail. The guardrail you never configured protected your open source; nothing protected the private stuff, which is where the secrets actually live.

Two more findings worth the price of admission: `permissions: {}` on the malicious workflow was used *by the attacker* — cosmetically, since secrets don't care — and about two-thirds of the implicated accounts have since vanished from GitHub, suggesting response is underway while the campaign kept evolving through October 24.

## The audit — five minutes, tonight

The radar: the commit message is searchable in public history, and it's noisy (legit `sync config` commits everywhere), so treat it as a lead generator, not a verdict:

```bash
gh api 'search/commits?q="ci: sync config"' --jq '.total_count'
# → 321 hits right now. Most are innocent sync scripts. Your job is the branch check below.
```

The actual self-audit — planted branches on your account (loop your repos, grep the branch pattern):

```bash
gh repo list --limit 200 --json nameWithOwner --jq '.[].nameWithOwner' | while read r; do
  gh api "repos/$r/branches" --paginate --jq '.[].name' 2>/dev/null | grep -E '^ci-sync-[0-9a-z]{6}$' && echo "  ↑ HIT in $r"
done
```

For **organizations** (org owners only — the audit-log API isn't available on personal accounts; the web UI's security log is the personal fallback):

```bash
# Workflow runs deleted within a minute of completing — Gheist's cleanup signature
gh api 'orgs/YOURORG/audit-log?include=all&phrase=workflow_run' \
  --jq '.[] | select(.action=="workflow_run.deleted")'
# The tool's user agent
gh api 'orgs/YOURORG/audit-log?include=all' --jq '.[] | select(.user_agent=="gheist")'
```

And the **cloud-side hunt that works even without GitHub logs** — Wiz's best trick: OIDC role assumptions whose session/subject contains `ci-sync-` (GitHub's OIDC subject includes the ref, so the planted branch name travels into your CloudTrail):

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --start-time 2026-09-15 --max-results 20 | grep -i 'ci-sync'
```

If anything hits: **rotate every secret that repo could see** — deleting runs doesn't un-dump them — revoke the pushing tokens, and check the token owners' machines for infostealers, because that's where the tokens came from.

## Harden for the next one

From Wiz's list, ranked by how little they cost: require **reviewers on environment-scoped secrets** (kills the environment matrix); scope OIDC trust policies to **protected branches only** (kills `ci-sync-*` role assumption); prefer **GitHub Apps or fine-grained, short-lived tokens** over classic PATs (shrinks what one stolen token reaches); run self-hosted runners **ephemerally, no Docker socket, no unrestricted metadata** (kills the host pivot). And never approve a held `sync-check` run sitting in `action_required` — that's the trap's front door.

## TL;DR

Gheist = stolen tokens + one two-line workflow + base32 + GitHub-as-C2, at a scale of 13,500 branches. Public repos got lucky via the first-contribution hold; private repos paid. The audit is five minutes of `gh` and one CloudTrail query — and if you run AI agents in CI, the campaign's shopping list literally names your provider. Check tonight.

Sources: [Wiz — Gheist: attempted scaled abuse of stolen GitHub tokens](https://www.wiz.io/blog/gheist-attempted-scaled-abuse-of-stolen-github-tokens-stumbles) · [CISA KEV / alerts hub](https://www.cisa.gov/news-events) · commit-search audit via `gh api` (commands above, verified live)