---
title: Database Concepts
tags:
  - developer-guide
  - concepts
  - database
---

# Database Concepts

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Overview

Tux uses a robust, async-first PostgreSQL database layer built with SQLModel and SQLAlchemy. The database architecture follows a clean three-layer pattern that separates concerns and enables maintainable, type-safe database operations.

The three layers work together to provide:

- **Service Layer**: Connection management, session handling, and health monitoring
- **Controller Layer**: Business logic, query optimization, and specialized operations
- **Model Layer**: Type-safe data models with automatic serialization and relationships

This architecture supports complex Discord bot operations including moderation, user leveling, custom commands, and configuration management, all while maintaining excellent performance and developer experience.

<!-- AUTO_INDEX_START -->
