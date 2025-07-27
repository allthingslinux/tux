# ADR Quick Reference Guide

## Creating a New ADR

### 1. Check if ADR is Needed

- [ ] Significant architectural change or addition
- [ ] Technology stack decision
- [ ] Design pattern standardization
- [ ] Cross-cutting concern affecting multiple modules

### 2. Create ADR File

```bash
# Copy template and rename with next number
cp docs/adr/template.md docs/adr/XXX-your-decision-title.md
```

### 3. Fill Out Template

- [ ] Clear problem statement in Context section
- [ ] Specific decision in Decision section
- [ ] Thorough alternatives analysis
- [ ] Realistic consequences assessment
- [ ] Actionable implementation plan

### 4. Submit for Review

- [ ] Set status to "Proposed"
- [ ] Add entry to ADR index in README.md
- [ ] Request technical review from 2 team members
- [ ] Share with development team for feedback

## Review Checklist

### Technical Review

- [ ] Problem clearly defined with context
- [ ] Decision is specific and actionable
- [ ] Alternatives thoroughly evaluated
- [ ] Implementation approach feasible
- [ ] Consequences realistically assessed
- [ ] Performance impact considered

### Team Review

- [ ] Implementation effort reasonable
- [ ] Integration points identified
- [ ] Developer experience implications clear
- [ ] Resource requirements realistic
- [ ] Timeline achievable

## Common ADR Patterns

### Technology Selection

```markdown
## Context
Current technology X has limitations Y and Z...

## Decision
Adopt technology A for use case B...

## Alternatives Considered
- Technology C: pros/cons
- Technology D: pros/cons
```

### Architecture Pattern

```markdown
## Context
Current architecture has coupling/complexity issues...

## Decision
Implement pattern X with components Y and Z...

## Implementation
Phase 1: Infrastructure
Phase 2: Migration
Phase 3: Optimization
```

### Process Standardization

```markdown
## Context
Inconsistent practices across team/codebase...

## Decision
Standardize on approach X with guidelines Y...

## Compliance
- Code review requirements
- Automated checks
- Documentation updates
```

## Status Management

### Status Meanings

- **Proposed**: Under review and discussion
- **Accepted**: Approved and ready for implementation
- **Rejected**: Not approved after review
- **Deprecated**: No longer relevant or applicable
- **Superseded**: Replaced by newer ADR

### Status Updates

```markdown
# Update status in ADR file
## Status
Accepted

# Update index in README.md
| ADR-001 | Title | Accepted | 2025-01-26 |

# Notify team of status change
```

## Implementation Tracking

### During Implementation

- [ ] Follow ADR implementation plan
- [ ] Verify compliance during code reviews
- [ ] Document any deviations or issues
- [ ] Update ADR if implementation reveals new information

### After Implementation

- [ ] Validate that implementation matches ADR intent
- [ ] Update ADR with lessons learned
- [ ] Create follow-up ADRs if needed
- [ ] Share implementation experience with team

## Common Mistakes to Avoid

### In ADR Creation

- ❌ Vague problem statements
- ❌ Solutions without alternatives analysis
- ❌ Unrealistic implementation timelines
- ❌ Missing consequences assessment
- ❌ No compliance mechanisms

### In Review Process

- ❌ Focusing only on technical details
- ❌ Not considering implementation effort
- ❌ Ignoring integration complexity
- ❌ Rushing through review process
- ❌ Not building team consensus

### In Implementation

- ❌ Deviating from ADR without discussion
- ❌ Not updating ADR with learnings
- ❌ Ignoring compliance requirements
- ❌ Not tracking implementation progress
- ❌ Forgetting to update documentation

## Useful Commands

### File Management

```bash
# Create new ADR
cp docs/adr/template.md docs/adr/006-new-decision.md

# Update ADR index
vim docs/adr/README.md

# Check ADR status
grep -r "## Status" docs/adr/*.md
```

### Review Process

```bash
# Find ADRs needing review
grep -l "Proposed" docs/adr/*.md

# Check implementation status
grep -A 5 "Implementation" docs/adr/*.md
```

## Getting Help

### Questions About Process

- Check [PROCESS.md](PROCESS.md) for detailed procedures
- Ask architecture team for guidance
- Review existing ADRs for examples

### Technical Questions

- Discuss with technical reviewers
- Bring to team meetings for broader input
- Consult with domain experts as needed

### Implementation Issues

- Reference ADR implementation section
- Discuss deviations with ADR author
- Update ADR if changes are needed

---

Keep this guide handy when working with ADRs. For detailed procedures, refer to the full [ADR Process Documentation](PROCESS.md).
