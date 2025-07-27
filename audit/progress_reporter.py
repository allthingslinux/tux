#!/usr/bin/env python3
"""
Progress Reporter
Generates comprehensive progress reports for the codebase improvement initiative
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
import subprocess
from jinja2 import Template

@dataclass
class Achievement:
    title: str
    description: str
    date: datetime
    impact: str  # 'high', 'medium', 'low'
    metrics_improved: List[str]

@dataclass
class Concern:
    title: str
    description: str
    severity: str  # 'high', 'medium', 'low'
    affected_metrics: List[str]
    recommended_action: str

@dataclass
class Recommendation:
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    estimated_effort: str  # 'low', 'medium', 'high'
    expected_impact: str  # 'high', 'medium', 'low'
    target_metrics: List[str]

class ProgressReporter:
    def __init__(self, metrics_db_path: str = "metrics.db"):
        self.metrics_db_path = metrics_db_path
        self.report_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Template]:
        """Load report templates
        weekly_template = """
# Weekly Progress Report - Week of {{ report_date.strftime('%B %d, %Y') }}

## Executive Summary
- **Overall Status**: {{ overall_status.title() }}
- **Key Achievements**: {{ achievements|length }} milestones reached
- **Areas of Concern**: {{ concerns|length }} items need attention
- **Trend**: {{ overall_trend.title() }}

## Metrics Dashboard

### Code Quality
| Metric | Current | Target | Status | Trend |
|--------|---------|--------|--------|-------|
{% for metric in quality_metrics %}
| {{ metric.display_name }} | {{ "%.1f"|format(metric.current) }}{{ metric.unit }} | {{ "%.1f"|format(metric.target) }}{{ metric.unit }} | {{ metric.status.title() }} | {{ metric.trend.title() }} |
{% endfor %}

### Performance
| Metric | Current | Target | Status | Trend |
|--------|---------|--------|--------|-------|
{% for metric in performance_metrics %}
| {{ metric.display_name }} | {{ "%.1f"|format(metric.current) }}{{ metric.unit }} | {{ "%.1f"|format(metric.target) }}{{ metric.unit }} | {{ metric.status.title() }} | {{ metric.trend.title() }} |
{% endfor %}

### Testing
| Metric | Current | Target | Status | Trend |
|--------|---------|--------|--------|-------|
{% for metric in testing_metrics %}
| {{ metric.display_name }} | {{ "%.1f"|format(metric.current) }}{{ metric.unit }} | {{ "%.1f"|format(metric.target) }}{{ metric.unit }} | {{ metric.status.title() }} | {{ metric.trend.title() }} |
{% endfor %}

## Achievements This Week
{% for achievement in achievements %}
### {{ achievement.title }}
{{ achievement.description }}

**Impact**: {{ achievement.impact.title() }}
**Metrics Improved**: {{ achievement.metrics_improved|join(', ') }}
**Date**: {{ achievement.date.strftime('%Y-%m-%d') }}

{% endfor %}

## Areas Requiring Attention
{% for concern in concerns %}
### {{ concern.title }} ({{ concern.severity.title() }} Priority)
{{ concern.description }}

**Affected Metrics**: {{ concern.affected_metrics|join(', ') }}
**Recommended Action**: {{ concern.recommended_action }}

{% endfor %}

## Recommendations for Next Week
{% for recommendation in recommendations %}
### {{ recommendation.title }} ({{ recommendation.priority.title() }} Priority)
{{ recommendation.description }}

**Estimated Effort**: {{ recommendation.estimated_effort.title() }}
**Expected Impact**: {{ recommendation.expected_impact.title() }}
**Target Metrics**: {{ recommendation.target_metrics|join(', ') }}

{% endfor %}

## Detailed Metrics History

### Trends Over Last 30 Days
{% for metric_name, history in historical_trends.items() %}
#### {{ metric_name.replace('_', ' ').title() }}
- **Current Value**: {{ "%.2f"|format(history.current_value) }}
- **30-Day Average**: {{ "%.2f"|format(history.avg_value) }}
- **Change**: {{ "%.1f"|format(history.change_percent) }}%
- **Trend**: {{ history.trend.title() }}

{% endfor %}

---
*Report generated on {{ report_date.strftime('%Y-%m-%d %H:%M:%S') }}*
"""

        monthly_template = """
# Monthly Progress Report - {{ report_date.strftime('%B %Y') }}

## Executive Summary
This report covers the progress made during {{ report_date.strftime('%B %Y') }} on the Tux Discord bot codebase improvement initiative.

### Overall Progress
- **Overall Status**: {{ overall_status.title() }}
- **Completed Milestones**: {{ completed_milestones }}
- **Active Improvements**: {{ active_improvements }}
- **Metrics Improved**: {{ improved_metrics_count }}

### Key Highlights
{% for highlight in key_highlights %}
- {{ highlight }}
{% endfor %}

## Monthly Metrics Summary

### Progress Against Goals
| Category | Metrics Meeting Target | Total Metrics | Success Rate |
|----------|----------------------|---------------|--------------|
{% for category in metric_categories %}
| {{ category.name }} | {{ category.meeting_target }} | {{ category.total }} | {{ "%.1f"|format(category.success_rate) }}% |
{% endfor %}

### Significant Changes This Month
{% for change in significant_changes %}
#### {{ change.metric_name.replace('_', ' ').title() }}
- **Previous Value**: {{ "%.2f"|format(change.previous_value) }}
- **Current Value**: {{ "%.2f"|format(change.current_value) }}
- **Change**: {{ "%.1f"|format(change.change_percent) }}%
- **Impact**: {{ change.impact }}

{% endfor %}

## Achievements This Month
{% for achievement in monthly_achievements %}
### {{ achievement.title }}
{{ achievement.description }}

**Date Completed**: {{ achievement.date.strftime('%Y-%m-%d') }}
**Impact Level**: {{ achievement.impact.title() }}
**Metrics Affected**: {{ achievement.metrics_improved|join(', ') }}

{% endfor %}

## Challenges and Resolutions
{% for challenge in challenges %}
### {{ challenge.title }}
**Challenge**: {{ challenge.description }}
**Resolution**: {{ challenge.resolution }}
**Lessons Learned**: {{ challenge.lessons_learned }}

{% endfor %}

## Next Month's Focus Areas
{% for focus_area in next_month_focus %}
### {{ focus_area.title }}
{{ focus_area.description }}

**Priority**: {{ focus_area.priority.title() }}
**Expected Outcomes**: {{ focus_area.expected_outcomes|join(', ') }}
**Resource Requirements**: {{ focus_area.resources }}

{% endfor %}

## Resource Utilization
- **Development Hours**: {{ resource_usage.dev_hours }} hours
- **Code Reviews**: {{ resource_usage.code_reviews }} reviews completed
- **Tests Added**: {{ resource_usage.tests_added }} new tests
- **Documentation Updates**: {{ resource_usage.docs_updated }} documents updated

---
*Report generated on {{ report_date.strftime('%Y-%m-%d %H:%M:%S') }}*
"""

        return {
            'weekly': Template(weekly_template),
            'monthly': Template(monthly_template)
        }

    def generate_weekly_report(self) -> str:
        """Generate weekly progress report"""
        report_data = self._collect_weekly_data()
        return self.report_templates['weekly'].render(**report_data)

    def generate_monthly_report(self) -> str:
        """Generate monthly progress report"""
        report_data = self._collect_monthly_data()
        return self.report_templates['monthly'].render(**report_data)

    def _collect_weekly_data(self) -> Dict[str, Any]:
        """Collect data for weekly report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Get latest metrics
        latest_metrics = self._get_latest_metrics()

        # Categorize metrics
        quality_metrics = self._filter_metrics(latest_metrics, ['test_coverage', 'type_coverage', 'avg_complexity', 'duplication_percentage'])
        performance_metrics = self._filter_metrics(latest_metrics, ['avg_response_time', 'p95_response_time', 'error_rate', 'memory_usage'])
        testing_metrics = self._filter_metrics(latest_metrics, ['test_count', 'flaky_test_rate'])

        # Get achievements, concerns, and recommendations
        achievements = self._identify_achievements(start_date, end_date)
        concerns = self._identify_concerns(latest_metrics)
        recommendations = self._generate_recommendations(latest_metrics, concerns)

        # Get historical trends
        historical_trends = self._get_historical_trends(30)

        # Calculate overall status and trend
        overall_status = self._calculate_overall_status(latest_metrics)
        overall_trend = self._calculate_overall_trend(historical_trends)

        return {
            'report_date': end_date,
            'overall_status': overall_status,
            'overall_trend': overall_trend,
            'quality_metrics': quality_metrics,
            'performance_metrics': performance_metrics,
            'testing_metrics': testing_metrics,
            'achievements': achievements,
            'concerns': concerns,
            'recommendations': recommendations,
            'historical_trends': historical_trends
        }

    def _collect_monthly_data(self) -> Dict[str, Any]:
        """Collect data for monthly report"""
        end_date = datetime.now()
        start_date = end_date.replace(day=1)  # First day of current month

        # Get monthly statistics
        monthly_stats = self._get_monthly_statistics(start_date, end_date)

        # Get significant changes
        significant_changes = self._identify_significant_changes(start_date, end_date)

        # Get monthly achievements
        monthly_achievements = self._identify_achievements(start_date, end_date)

        # Get challenges and resolutions
        challenges = self._get_challenges_and_resolutions(start_date, end_date)

        # Plan next month's focus
        next_month_focus = self._plan_next_month_focus()

        # Get resource utilization
        resource_usage = self._calculate_resource_usage(start_date, end_date)

        return {
            'report_date': end_date,
            'overall_status': monthly_stats['overall_status'],
            'completed_milestones': monthly_stats['completed_milestones'],
            'active_improvements': monthly_stats['active_improvements'],
            'improved_metrics_count': monthly_stats['improved_metrics_count'],
            'key_highlights': monthly_stats['key_highlights'],
            'metric_categories': monthly_stats['metric_categories'],
            'significant_changes': significant_changes,
            'monthly_achievements': monthly_achievements,
            'challenges': challenges,
            'next_month_focus': next_month_focus,
            'resource_usage': resource_usage
        }

    def _get_latest_metrics(self) -> List[Dict[str, Any]]:
        """Get latest metrics from database"""
        if not os.path.exists(self.metrics_db_path):
            return []

        with sqlite3.connect(self.metrics_db_path) as conn:
            cursor = conn.execute("""
                SELECT metric_name, value, target, status, trend, timestamp
                FROM metrics m1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM metrics m2
                    WHERE m2.metric_name = m1.metric_name
                )
                ORDER BY metric_name
            """)

            metrics = []
            for row in cursor.fetchall():
                metrics.append({
                    'name': row[0],
                    'display_name': row[0].replace('_', ' ').title(),
                    'current': row[1],
                    'target': row[2],
                    'status': row[3],
                    'trend': row[4],
                    'timestamp': row[5],
                    'unit': self._get_metric_unit(row[0])
                })

            return metrics

    def _get_metric_unit(self, metric_name: str) -> str:
        """Get appropriate unit for metric"""
        units = {
            'test_coverage': '%',
            'type_coverage': '%',
            'duplication_percentage': '%',
            'error_rate': '%',
            'flaky_test_rate': '%',
            'avg_response_time': 'ms',
            'p95_response_time': 'ms',
            'memory_usage': 'MB',
            'avg_complexity': '',
            'test_count': ''
        }
        return units.get(metric_name, '')

    def _filter_metrics(self, metrics: List[Dict], metric_names: List[str]) -> List[Dict]:
        """Filter metrics by names"""
        return [m for m in metrics if m['name'] in metric_names]

    def _identify_achievements(self, start_date: datetime, end_date: datetime) -> List[Achievement]:
        """Identify achievements in the given period"""
        achievements = []

        # Check for metrics that improved significantly
        with sqlite3.connect(self.metrics_db_path) as conn:
            cursor = conn.execute("""
                SELECT metric_name,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       AVG(value) as avg_value
                FROM metrics
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY metric_name
            """, (start_date.isoformat(), end_date.isoformat()))

            for row in cursor.fetchall():
                metric_name, min_val, max_val, avg_val = row

                # Check if metric improved significantly
                if metric_name in ['test_coverage', 'type_coverage']:
                    if max_val > min_val + 5:  # 5% improvement
                        achievements.append(Achievement(
                            title=f"Significant {metric_name.replace('_', ' ').title()} Improvement",
                            description=f"{metric_name.replace('_', ' ').title()} improved from {min_val:.1f}% to {max_val:.1f}%",
                            date=end_date,
                            impact='high',
                            metrics_improved=[metric_name]
                        ))
                elif metric_name in ['avg_complexity', 'duplication_percentage', 'error_rate']:
                    if min_val < max_val - 2:  # Significant reduction
                        achievements.append(Achievement(
                            title=f"Reduced {metric_name.replace('_', ' ').title()}",
                            description=f"{metric_name.replace('_', ' ').title()} reduced from {max_val:.1f} to {min_val:.1f}",
                            date=end_date,
                            impact='medium',
                            metrics_improved=[metric_name]
                        ))

        # Add milestone achievements
        milestones = self._check_milestone_achievements()
        achievements.extend(milestones)

        return achievements

    def _check_milestone_achievements(self) -> List[Achievement]:
        """Check for milestone achievements"""
        milestones = []
        latest_metrics = self._get_latest_metrics()

        for metric in latest_metrics:
            if metric['status'] == 'excellent' and metric['name'] == 'test_coverage':
                if metric['current'] >= 90:
                    milestones.append(Achievement(
                        title="90% Test Coverage Milestone Reached",
                        description="The codebase has achieved 90% test coverage, meeting our quality target",
                        date=datetime.now(),
                        impact='high',
                        metrics_improved=['test_coverage']
                    ))

        return milestones

    def _identify_concerns(self, metrics: List[Dict]) -> List[Concern]:
        """Identify areas of concern based on current metrics"""
        concerns = []

        for metric in metrics:
            if metric['status'] == 'needs_improvement':
                severity = 'high' if metric['trend'] == 'declining' else 'medium'

                concerns.append(Concern(
                    title=f"Poor {metric['display_name']} Performance",
                    description=f"{metric['display_name']} is at {metric['current']:.1f}{metric['unit']}, below target of {metric['target']:.1f}{metric['unit']}",
                    severity=severity,
                    affected_metrics=[metric['name']],
                    recommended_action=self._get_recommended_action(metric['name'])
                ))

        return concerns

    def _get_recommended_action(self, metric_name: str) -> str:
        """Get recommended action for improving a metric"""
        actions = {
            'test_coverage': 'Add unit tests for uncovered code paths, focus on critical business logic',
            'type_coverage': 'Add type hints to function signatures and variable declarations',
            'avg_complexity': 'Refactor complex functions into smaller, more focused methods',
            'duplication_percentage': 'Extract common code into shared utilities and services',
            'avg_response_time': 'Profile slow operations and optimize database queries',
            'error_rate': 'Improve error handling and add more comprehensive validation',
            'flaky_test_rate': 'Investigate and fix unstable tests, improve test isolation'
        }
        return actions.get(metric_name, 'Review and improve this metric')

    def _generate_recommendations(self, metrics: List[Dict], concerns: List[Concern]) -> List[Recommendation]:
        """Generate recommendations based on current state"""
        recommendations = []

        # High-priority recommendations based on concerns
        for concern in concerns:
            if concern.severity == 'high':
                recommendations.append(Recommendation(
                    title=f"Address {concern.title}",
                    description=concern.recommended_action,
                    priority='high',
                    estimated_effort='medium',
                    expected_impact='high',
                    target_metrics=concern.affected_metrics
                ))

        # General improvement recommendations
        improving_metrics = [m for m in metrics if m['trend'] == 'improving']
        if improving_metrics:
            recommendations.append(Recommendation(
                title="Continue Current Improvement Momentum",
                description=f"Several metrics are improving: {', '.join([m['display_name'] for m in improving_metrics[:3]])}. Continue current practices.",
                priority='medium',
                estimated_effort='low',
                expected_impact='medium',
                target_metrics=[m['name'] for m in improving_metrics]
            ))

        return recommendations

    def _get_historical_trends(self, days: int) -> Dict[str, Any]:
        """Get historical trends for metrics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        trends = {}

        with sqlite3.connect(self.metrics_db_path) as conn:
            cursor = conn.execute("""
                SELECT metric_name, value, timestamp
                FROM metrics
                WHERE timestamp >= ?
                ORDER BY metric_name, timestamp
            """, (start_date.isoformat(),))

            metric_data = {}
            for row in cursor.fetchall():
                metric_name, value, timestamp = row
                if metric_name not in metric_data:
                    metric_data[metric_name] = []
                metric_data[metric_name].append((timestamp, value))

        for metric_name, data_points in metric_data.items():
            if len(data_points) >= 2:
                values = [point[1] for point in data_points]
                current_value = values[-1]
                avg_value = sum(values) / len(values)
                change_percent = ((current_value - values[0]) / values[0]) * 100 if values[0] != 0 else 0

                if abs(change_percent) < 2:
                    trend = 'stable'
                elif change_percent > 0:
                    trend = 'improving' if metric_name in ['test_coverage', 'type_coverage'] else 'declining'
                else:
                    trend = 'declining' if metric_name in ['test_coverage', 'type_coverage'] else 'improving'

                trends[metric_name] = {
                    'current_value': current_value,
                    'avg_value': avg_value,
                    'change_percent': change_percent,
                    'trend': trend
                }

        return trends

    def _calculate_overall_status(self, metrics: List[Dict]) -> str:
        """Calculate overall project status"""
        if not metrics:
            return 'unknown'

        excellent_count = sum(1 for m in metrics if m['status'] == 'excellent')
        good_count = sum(1 for m in metrics if m['status'] == 'good')
        total_count = len(metrics)

        excellent_ratio = excellent_count / total_count
        good_or_better_ratio = (excellent_count + good_count) / total_count

        if excellent_ratio >= 0.8:
            return 'excellent'
        elif good_or_better_ratio >= 0.7:
            return 'good'
        else:
            return 'needs_improvement'

    def _calculate_overall_trend(self, trends: Dict[str, Any]) -> str:
        """Calculate overall trend across all metrics"""
        if not trends:
            return 'stable'

        improving_count = sum(1 for t in trends.values() if t['trend'] == 'improving')
        declining_count = sum(1 for t in trends.values() if t['trend'] == 'declining')
        total_count = len(trends)

        if improving_count > declining_count * 1.5:
            return 'improving'
        elif declining_count > improving_count * 1.5:
            return 'declining'
        else:
            return 'stable'

    def save_report(self, report_content: str, report_type: str, output_dir: str = "reports"):
        """Save report to file"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_report_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            f.write(report_content)

        print(f"Report saved to {filepath}")
        return filepath

def main():
    """Main function to generate reports"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate progress reports')
    parser.add_argument('--type', choices=['weekly', 'monthly'], default='weekly',
                       help='Type of report to generate')
    parser.add_argument('--output-dir', default='reports',
                       help='Output directory for reports')

    args = parser.parse_args()

    reporter = ProgressReporter()

    if args.type == 'weekly':
        print("Generating weekly progress report...")
        report = reporter.generate_weekly_report()
    else:
        print("Generating monthly progress report...")
        report = reporter.generate_monthly_report()

    # Save report
    filepath = reporter.save_report(report, args.type, args.output_dir)

    # Also print to stdout
    print("\n" + "="*80)
    print(report)

if __name__ == '__main__':
    main()
