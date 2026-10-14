# Security

This is a local, single-tenant starter with read-only demo tools. It does not include per-user authorization, distributed locking, write approvals, or a retention service.

Use localhost for the default unauthenticated mode. Set a shared API token before any trusted-network deployment, and implement user-level authorization before serving multiple users. Treat checkpoint files as sensitive: they contain conversation and tool content.

Do not submit real API keys, personal information, or exploit details in public issues. If the repository offers GitHub's private vulnerability reporting feature, use it. Otherwise contact the maintainer through an available private channel before sharing sensitive details. Private vulnerability reporting is not enabled by this source change.
