# Consistency Checking Procedures for Assessments

## Overview
This document defines procedures for ensuring consistent assessment of impact and effort scores across all improvement items.

## Assessment Consistency Framework

### Scoring Calibration Standards

#### Impact Assessment Calibration (1-10 Scale)

**User Experience Impact**
- **1-2 (Minimal)**: Internal changes with no direct user-facing impact
- **3-4 (Low)**: Minor improvements to user experience or edge case fixes
- **5-6 (Medium)**: Noticeable improvements to common user workflows
- **7-8 (High)**: Significant improvements to core user functionality
- **9-10 (Critical)**: Major user experience transformations or critical fixes

**Developer Productivity Impact**
- **1-2 (Minimal)**: Minor code organization improvements
- **3-4 (Low)**: Small improvements to development workflow
- **5-6 (Medium)**: Moderate reduction in development time or complexity
- **7-8 (High)**: Significant improvements to development speed/ease
- **9-10 (Critical)**: Major productivity gains or elimination of major pain points

**System Reliability Impact**
- **1-2 (Minimal)**: Minor logging or monitoring improvements
- **3-4 (Low)**: Small improvements to error handling or stability
- **5-6 (Medium)**: Moderate improvements to system robustness
- **7-8 (High)**: Significant reliability or performance improvements
- **9-10 (Critical)**: Major stability improvements or critical bug fixes

**Technical Debt Reduction Impact**
- **1-2 (Minimal)**: Minor code cleanup or documentation
- **3-4 (Low)**: Small refactoring or pattern improvements
- **5-6 (Medium)**: Moderate architectural improvements
- **7-8 (High)**: Significant debt reduction or pattern standardization
- **9-10 (Critical)**: Major architectural improvements or legacy elimination

#### Effort Assessment Calibration (1-10 Scale)

**Technical Complexity**
- **1-2 (Simple)**: Straightforward changes with well-known patterns
- **3-4 (Low)**: Minor refactoring or configuration changes
- **5-6 (Medium)**: Moderate complexity requiring some research/design
- **7-8 (High)**: Complex changes requiring significant design work
- **9-10 (Very High)**: Highly complex changes with unknown challenges

**Dependencies**
- **1-2 (None)**: Standalone changes with no external dependencies
- **3-4 (Few)**: 1-2 minor dependencies on other components
- **5-6 (Some)**: 3-5 dependencies or coordination with other teams
- **7-8 (Many)**: Multiple complex dependencies or external integrations
- **9-10 (Extensive)**: Extensive dependencies requiring coordinated changes

**Risk Level**
- **1-2 (Very Low)**: Well-understood changes with minimal risk
- **3-4 (Low)**: Minor risk of breaking changes or complications
- **5-6 (Medium)**: Moderate risk requiring careful testing
- **7-8 (High)**: High risk of breaking changes or system impact
- **9-10 (Very High)**: Very high risk requiring extensive validation

**Resource Requirements**
- **1-2 (Minimal)**: 1-2 days of work by single developer
- **3-4 (Low)**: 1 week of work by single developer
- **5-6 (Medium)**: 2-4 weeks of work or multiple developers
- **7-8 (High)**: 1-2 months of work or specialized expertise
- **9-10 (Very High)**: 3+ months of work or extensive team involvement

## Consistency Checking Procedures

### Procedure 1: Calibration Session
**Purpose**: Establish consistent understanding of scoring criteria
**Frequency**: Before beginning assessments
**Process**:
1. Review calibration standards with all assessors
2. Practice scoring 5-10 sample improvements together
3. Discuss and align on scoring rationale
4. Document any clarifications or adjustments to standards

### Procedure 2: Parallel Assessment
**Purpose**: Validate consistency between assessors
**Frequency**: For first 10 assessments and every 20th assessment thereafter
**Process**:
1. Two assessors independently score the same improvement
2. Compare scores and identify discrepancies (>2 point difference)
3. Discuss rationale and reach consensus
4. Document lessons learned and update calibration if needed

### Procedure 3: Cross-Category Consistency Check
**Purpose**: Ensure consistent scoring across different improvement categories
**Frequency**: After completing each category of improvements
**Process**:
1. Review all scores within the category for internal consistency
2. Compare category averages against other categories
3. Identify outliers or inconsistencies
4. Re-assess outliers if necessary

### Procedure 4: Historical Comparison
**Purpose**: Maintain consistency over time as more assessments are completed
**Frequency**: Weekly during assessment phase
**Process**:
1. Compare recent assessments against earlier ones
2. Look for scoring drift or inconsistencies
3. Re-calibrate if systematic differences are found
4. Update documentation with lessons learned

## Consistency Validation Methods

### Statistical Consistency Checks

**Inter-Rater Reliability**
- Calculate correlation between parallel assessments
- Target: >0.8 correlation for overall scores
- Flag assessments with >2 point discrepancies for review

**Score Distribution Analysis**
- Monitor distribution of scores across all assessments
- Identify unusual patterns (e.g., too many 5s, no extreme scores)
- Compare distributions across categories and time periods

**Outlier Detection**
- Identify improvements with unusual score combinations
- Flag for expert review if scores don't align with typical patterns
- Document rationale for confirmed outliers

### Qualitative Consistency Reviews

**Rationale Review**
- Review written justifications for scoring decisions
- Ensure rationale aligns with calibration standards
- Identify and address inconsistent reasoning patterns

**Category Comparison**
- Compare similar improvements across different categories
- Ensure similar improvements receive similar scores
- Document and resolve any inconsistencies found

**Expert Validation**
- Have domain experts review a sample of assessments
- Validate that scores align with technical understanding
- Incorporate expert feedback into calibration standards

## Quality Assurance Metrics

### Consistency Metrics
- **Inter-Rater Correlation**: Target >0.8 for parallel assessments
- **Score Variance**: Monitor variance within similar improvement types
- **Calibration Drift**: Track changes in scoring patterns over time

### Quality Metrics
- **Assessment Completion Rate**: % of assessments completed on schedule
- **Revision Rate**: % of assessments requiring revision after review
- **Expert Validation Score**: Expert rating of assessment quality

### Process Metrics
- **Calibration Session Effectiveness**: Improvement in consistency after calibration
- **Review Cycle Time**: Time required for consistency checking procedures
- **Issue Resolution Rate**: % of consistency issues successfully resolved

## Remediation Procedures

### When Inconsistencies Are Found

**Minor Inconsistencies (1-2 point differences)**
1. Review rationale and calibration standards
2. Discuss with original assessor
3. Reach consensus on correct score
4. Update assessment documentation

**Major Inconsistencies (>2 point differences)**
1. Escalate to assessment lead or expert reviewer
2. Conduct detailed review of both assessments
3. Re-assess using calibration standards
4. Update process documentation if needed

**Systematic Inconsistencies**
1. Identify root cause (unclear standards, assessor training, etc.)
2. Update calibration standards or provide additional training
3. Re-assess affected improvements if necessary
4. Implement additional quality checks

## Success Criteria

### Individual Assessment Level
- Scores align with calibration standards
- Written rationale supports scoring decisions
- Consistent scoring for similar improvements

### Process Level
- >0.8 inter-rater correlation for parallel assessments
- <10% revision rate after consistency review
- Expert validation score >8/10

### Overall Quality Level
- Consistent scoring patterns across all categories
- Stakeholder confidence in assessment accuracy
- Successful completion of all consistency checks
