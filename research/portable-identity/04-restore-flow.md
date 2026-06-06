# Portable Identity UX — Node Re-Association After Restore

**Issue**: #307
**Date**: 2026-05-24

---

## The Re-Association Problem

When an operator restores their identity on a new machine, their previously registered
nodes still exist in the directory's `node_operators` table linked to their `operator_id`.
The operator needs to:
1. Verify which nodes are linked to the restored identity
2. Re-configure the new machine to control those nodes
3. Re-issue node_tokens if the previous tokens were stored only on the lost machine

---

## Directory-Side: operator_id Lookup

The directory already links nodes to operators via `operator_id` (stored during `POST /v1/register`).
A restored identity with the same `operator_id` can immediately query its linked nodes.

**Proposed endpoint** (currently missing — needed for wizard "Found N nodes" display):
```
GET /api/v1/identity/nodes
Authorization: Bearer <operator_token>

Response:
{
  "operator_id": "iop_7xK9mN2vFqRsPbAeYtLwCdZuJ3hGnX8W",
  "nodes": [
    {
      "node_id": "...",
      "endpoint": "https://eu-node.example.com:9484",
      "region": "eu-central",
      "last_seen": "2026-05-24T09:35:00Z",
      "status": "active",
      "reputation_score": 0.87
    }
  ]
}
```

This endpoint lets the wizard show "Found 3 nodes linked to your identity" immediately
after a successful restore.

---

## Re-Association Flow

### Scenario A: Nodes still running (machine lost, nodes intact)

The nodes continue to send heartbeats with their existing node_tokens. The operator
only needs to restore their identity on the new admin machine.

```bash
# On new machine
iicp-node identity import --phrase "canyon drift..."
iicp-node status  # shows all linked nodes
iicp-node node add --import <node_id>  # imports node config (endpoint, token) from directory
```

The nodes themselves do not need to be touched. Re-association is complete in < 1 minute.

### Scenario B: Nodes lost (machine AND nodes lost)

The operator must re-register each node from scratch on new hardware. However:
- The `operator_id` is preserved via identity restore
- Previously accumulated reputation is preserved (linked to `operator_id`)
- The operator re-registers nodes under the same `operator_id` → reputation continues

```bash
# Restore identity
iicp-node identity import --phrase "canyon drift..."

# On each new node machine
iicp-node register \
  --endpoint https://new-eu-node.example.com:9484 \
  --operator-key ~/.iicp/operator.key

# The directory links the new node to the existing operator_id
# Previous reputation score is re-associated
```

**Important**: Reputation is linked to the node's `node_id`, not the `operator_id` directly.
If the node hardware is lost, reputation accumulated on that node_id is NOT automatically
transferred to a new node_id. The operator starts a new node at sc=0.50. This is intentional
— reputation represents the specific node's track record, not the operator's abstract identity.

**What IS preserved on identity restore**: The operator's ability to administer all previously
registered nodes, their attestation status (ADR-030 T2), and any operator-level credits.

---

## Cross-Device: Same Identity, Multiple Admin Machines

The `operator.key` file can be on multiple machines simultaneously. This is fine:
- Both machines can issue operator_token JWTs
- Both machines can register new nodes under the same operator_id
- Key revocation (if key is compromised) requires a separate `iicp-node identity revoke` flow

**Practical pattern**: The key file lives in a password manager's "secure note" attachment,
synced across devices. Or synced via a trusted secrets manager (Vault, 1Password SSH agent, etc.).

---

## Time to Re-Association

| Scenario | Time estimate |
|----------|-------------|
| Identity restore + list nodes | < 1 minute |
| Node still running, import config | < 2 minutes total |
| New node registration with existing identity | < 5 minutes |
| Full disaster recovery (identity + all nodes) | < 30 minutes per node |

The 30-day identity-age preservation (REP2 platinum clock) means disaster recovery
doesn't reset the operator's access level. They pick up where they left off.
