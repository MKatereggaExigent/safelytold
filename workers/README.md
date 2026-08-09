# Background workers

The workers are deliberately separated from the HTTP services.

- `workflow_worker`: Temporal workflows and activities for case lifecycle, retaliation safeguards, disclosures and retention.
- `outbox_relay`: publishes privacy-safe transactional outbox records to RabbitMQ.
- `event_consumer`: reference idempotent consumer with dead-letter handling.
- `prefect_flows`: governed AI/data pipelines that never own authoritative case state.

Temporal owns long-running business state. RabbitMQ distributes notifications and integration events. Prefect owns batch/data/AI orchestration.
