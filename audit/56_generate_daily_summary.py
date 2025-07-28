#!/usr/bin/env python3
"""
Daily Summary Generator
Creates concise daily summaries of key metrics and changes
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DailySummaryGenerator:
    def __init__(self, metrics_db_path: str = "metrics.db"):
        self.metrics_db_path = metrics_db_path

    def generate_daily_summary(self) -> Dict[str, Any]:
        """Generate daily summary of key metrics and changes"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        summary = {
            'date': today.strftime('%Y-%m-%d'),
            'overall_status': self._get_overall_status(),
            'key_metrics': self._get_key_metrics(),
            'daily_changes': self._get_daily_changes(yesterday, today),
            'alerts': self._check_alerts(),
            'quick_wins': self._identify_quick_wins(),
            'action_items': self._get_action_items()
        }

        return summary

    def _get_overall_status(self) -> str:
        """Get overall project status"""
        if not os.path.exists(self.metrics_db_path):
            return 'unknown'

        with sqlite3.connect(self.metrics_db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM metrics m1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM metrics m2
                    WHERE m2.metric_name = m1.metric_name
                )
                GROUP BY status
            """)

            status_counts = dict(cursor.fetchall())
            total = sum(status_counts.values())

            if not total:
                return 'unknown'

            excellent_ratio = status_counts.get('excellent', 0) / total
            good_ratio = status_counts.get('good', 0) / total

            if excellent_ratio >= 0.8:
                return 'excellent'
            elif (excellent_ratio + good_ratio) >= 0.7:
                return 'good'
            else:
                return 'needs_improvement'

    def _get_key_metrics(self) -> List[Dict[str, Any]]:
        """Get current values of key metrics"""
        key_metric_names = [
            'test_coverage', 'error_rate', 'avg_response_time',
            'duplication_percentage', 'avg_complexity'
        ]

        metrics = []

        if not os.path.exists(self.metrics_db_path):
            return metrics

        with sqlite3.connect(self.metrics_db_path) as conn:
            for metric_name in key_metric_names:
                cursor = conn.execute("""
                    SELECT value, target, status, trend
                    FROM metrics
                    WHERE metric_name = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (metric_name,))

                row = cursor.fetchone()
   if row:
                    metrics.append({
                        'name': metric_name,
                        'display_name': metric_name.replace('_', ' ').title(),
                        'value': row[0],
                        'target': row[1],
                        'status': row[2],
                        'trend': row[3],
                        'unit': self._get_metric_unit(metric_name)
                    })

        return metrics

    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for metric"""
        units = {
            'test_coverage': '%',
            'error_rate': '%',
            'avg_response_time': 'ms',
            'duplication_percentage': '%',
            'avg_complexity': ''
        }
        return units.get(metric_name, '')

    def _get_daily_changes(self, yesterday: datetime, today: datetime) -> List[Dict[str, Any]]:
        """Get significant changes from yesterday to today"""
        changes = []

        if not os.path.exists(self.metrics_db_path):
            return changes

        with sqlite3.connect(self.metrics_db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    metric_name,
                    value as today_value,
                    LAG(value) OVER (PARTITION BY metric_name ORDER BY timestamp) as yesterday_value
                FROM metrics
                WHERE DATE(timestamp) IN (?, ?)
                ORDER BY metric_name, timestamp DESC
            """, (yesterday.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')))

            for row in cursor.fetchall():
                metric_name, today_val, yesterday_val = row

                if yesterday_val is not None and today_val != yesterday_val:
                    change_percent = ((today_val - yesterday_val) / yesterday_val) * 100 if yesterday_val != 0 else 0

                    if abs(change_percent) > 5:  # Only report significant changes
                        changes.append({
                            'metric': metric_name.replace('_', ' ').title(),
                            'yesterday': yesterday_val,
                            'today': today_val,
                            'change_percent': change_percent,
                            'direction': 'improved' if self._is_improvement(metric_name, change_percent) else 'declined'
                        })

        return changes

    def _is_improvement(self, metric_name: str, change_percent: float) -> bool:
        """Determine if a change is an improvement"""
        # For metrics where higher is better
        if metric_name in ['test_coverage', 'type_coverage']:
            return change_percent > 0
        # For metrics where lower is better
        else:
            return change_percent < 0

    def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []

        key_metrics = self._get_key_metrics()

        for metric in key_metrics:
            # High priority alerts
            if metric['name'] == 'error_rate' and metric['value'] > 2.0:
                alerts.append({
                    'severity': 'high',
                    'message': f"Error rate is {metric['value']:.1f}%, above 2% threshold",
                    'metric': metric['name']
                })

            elif metric['name'] == 'test_coverage' and metric['value'] < 80.0:
                alerts.append({
                    'severity': 'medium',
                    'message': f"Test coverage is {metric['value']:.1f}%, below 80% threshold",
                    'metric': metric['name']
                })

            elif metric['name'] == 'avg_response_time' and metric['value'] > 500.0:
                alerts.append({
                    'severity': 'high',
                    'message': f"Average response time is {metric['value']:.1f}ms, above 500ms threshold",
                    'metric': metric['name']
                })

        return alerts

    def _identify_quick_wins(self) -> List[str]:
        """Identify potential quick wins based on current metrics"""
        quick_wins = []

        key_metrics = self._get_key_metrics()

        for metric in key_metrics:
            if metric['status'] == 'good' and metric['trend'] == 'improving':
                if metric['name'] == 'test_coverage' and metric['value'] > 85:
                    quick_wins.append("Test coverage is close to 90% target - add a few more tests to reach excellent status")

                elif metric['name'] == 'duplication_percentage' and metric['value'] < 7:
                    quick_wins.append("Code duplication is low - small refactoring effort could reach excellent status")

        return quick_wins

    def _get_action_items(self) -> List[str]:
        """Get recommended action items for today"""
        actions = []

        # Check for metrics that need immediate attention
        key_metrics = self._get_key_metrics()

        needs_improvement = [m for m in key_metrics if m['status'] == 'needs_improvement']

        if needs_improvement:
            actions.append(f"Focus on improving {len(needs_improvement)} metrics in 'needs improvement' status")

        declining_metrics = [m for m in key_metrics if m['trend'] == 'declining']

        if declining_metrics:
            actions.append(f"Investigate {len(declining_metrics)} metrics showing declining trends")

        # Add specific actions based on alerts
        alerts = self._check_alerts()
        high_priority_alerts = [a for a in alerts if a['severity'] == 'high']

        if high_priority_alerts:
            actions.append(f"Address {len(high_priority_alerts)} high-priority alerts immediately")

        return actions

    def format_summary_text(self, summary: Dict[str, Any]) -> str:
        """Format summary as readable text"""
        text = f"""# Daily Metrics Summary - {summary['date']}

## Overall Status: {summary['overall_status'].title()}

## Key Metrics
"""

        for metric in summary['key_metrics']:
            status_emoji = {'excellent': '🟢', 'good': '🟡', 'needs_improvement': '🔴'}.get(metric['status'], '⚪')
            trend_emoji = {'improving': '📈', 'stable': '➡️', 'declining': '📉'}.get(metric['trend'], '➡️')

            text += f"- {status_emoji} **{metric['display_name']}**: {metric['value']:.1f}{metric['unit']} (target: {metric['target']:.1f}{metric['unit']}) {trend_emoji}\n"

        if summary['daily_changes']:
            text += "\n## Daily Changes\n"
            for change in summary['daily_changes']:
                direction_emoji = '📈' if change['direction'] == 'improved' else '📉'
                text += f"- {direction_emoji} **{change['metric']}**: {change['yesterday']:.1f} → {change['today']:.1f} ({change['change_percent']:+.1f}%)\n"

        if summary['alerts']:
            text += "\n## Alerts\n"
            for alert in summary['alerts']:
                severity_emoji = {'high': '🚨', 'medium': '⚠️', 'low': 'ℹ️'}.get(alert['severity'], 'ℹ️')
                text += f"- {severity_emoji} {alert['message']}\n"

        if summary['quick_wins']:
            text += "\n## Quick Wins\n"
            for win in summary['quick_wins']:
                text += f"- 💡 {win}\n"

        if summary['action_items']:
            text += "\n## Action Items for Today\n"
            for action in summary['action_items']:
                text += f"- ✅ {action}\n"

        text += f"\n---\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return text

def main():
    """Generate and save daily summary"""
    generator = DailySummaryGenerator()

    print("Generating daily summary...")
    summary = generator.generate_daily_summary()

    # Save JSON version
    with open('daily_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    # Save text version
    text_summary = generator.format_summary_text(summary)
    with open('daily_summary.md', 'w') as f:
        f.write(text_summary)

    print("Daily summary generated:")
    print(f"- Overall status: {summary['overall_status']}")
    print(f"- Alerts: {len(summary['alerts'])}")
    print(f"- Daily changes: {len(summary['daily_changes'])}")
    print(f"- Quick wins: {len(summary['quick_wins'])}")
    print(f"- Action items: {len(summary['action_items'])}")

    # Print summary to console
    print("\n" + "="*60)
    print(text_summary)

if __name__ == '__main__':
    main()
