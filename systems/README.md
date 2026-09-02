# Systems

Persistent operational infrastructure.

This public template intentionally does not ship a full private tooling stack. Instead, it defines the role of the systems layer so users can build their own.

Use this layer for:

- scripts
- agents
- automations
- dashboards
- validation tooling
- workflow helpers

The rule is simple:

Do not automate what you do not yet understand.

Build tools only after the human workflow is clear enough to preserve in code.

For public contributions, executable tooling, agent prompts, workflows, migrations, and dependencies are high-risk changes. They should include synthetic fixtures, validation notes, and rollback notes. See [`../docs/proposal-lifecycle.md`](../docs/proposal-lifecycle.md) and [`../docs/private-sync-protocol.md`](../docs/private-sync-protocol.md).
