---
name: risk-based-testing-with-code-health
description: Use when a user asks what to test first based on CodeScene findings, especially for high-risk hotspots or pull-request change sets.
---

# Risk-Based Testing With Code Health

## Overview
Use this skill when the goal is to turn CodeScene risk signals into practical testing priorities.
The output should help testers and developers focus limited test time on the code most likely to produce defects.

The primary signal is always the **current branch's change set** — what has actually changed is more immediately actionable than historical hotspots. Hotspots provide background context and catch systemic risk, but they should not displace focus from files the branch has already touched.

## When to Use
- A user asks where testing should focus based on CodeScene hotspots.
- A user asks for a tester-friendly test plan from technical debt or code health findings.
- A user wants pull-request risk translated into concrete test scenarios.
- A release owner asks for risk-based regression scope before ship.

Do not use this skill when the user only asks for conceptual definitions of Code Health.
Use `explaining-code-health` for fundamentals.

... (copied content)
