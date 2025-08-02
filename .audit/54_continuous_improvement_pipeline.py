#!/usr/bin/env python3
"""
Continuous Improvement Pipeline
Implements automated feedback loops and improvement suggestions
"""

import json
import sqlite3
import os
import subprocess
froimport datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests
from pathlib import Path

@dataclass
class ImprovementSuggestion:
    id: Optional[int]
    title: str
    description: str
    category: str  # 'code_quality', 'performance', 'testing', 'security'
    priority: str  # 'high', 'medium', 'low'
    estimated_effort: str  # 'low', 'medium', 'high'
    expected_impact: str  # 'high', 'medium', 'low'
    affected_files: List[str]
    metrics_impact: List[str]
    created_at: datetime
    status: str  # 'open', 'in_progress', 'completed', 'rejected'
    assignee: Optional[str] = None

@dataclass
class FeedbackItem:
    id: Optional[int]
    source: str  # 'developer', 'automated', 'metrics'
    feedback_type: str  # 'suggestion', 'issue', 'praise'
    title: str
    description: str
    priority: int  # 1-5 scale
    created_at: datetime
    status: str  # 'open', 'reviewed', 'implemented', 'rejected'

class ContinuousImprovementPipeline:
    def __init__(self, db_path: str = "improvement_pipeline.db"):
        self.db_path = db_path
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO', 'AllTux/tux')
        self._init_database()

    def _init_database(self):
        """Initialize the improvement pipeline database"""
        with sqlite3.connect(self.db_path) as conn:
            # Suggestions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    estimated_effort TEXT NOT NULL,
                    expected_impact TEXT NOT NULL,
                    affected_files TEXT NOT NULL,
                    metrics_impact TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assignee TEXT
                )
            """)

            # Feedback table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)

            # Performance baselines table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_name TEXT NOT NULL UNIQUE,
                    mean_time REAL NOT NULL,
                    std_deviation REAL NOT NULL,
                    p95_time REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)

    def analyze_codebase_for_improvements(self) -> List[ImprovementSuggestion]:
        """Analyze codebase and generate improvement suggestions"""
        suggestions = []

        # Analyze code duplication
        suggestions.extend(self._analyze_code_duplication())

        # Analyze complexity issues
        suggestions.extend(self._analyze_complexity_issues())

        # Analyze test coverage gaps
        suggestions.extend(self._analyze_test_coverage_gaps())

        # Analyze performance opportunities
        suggestions.extend(self._analyze_performance_opportunities())

        # Analyze security issues
        suggestions.extend(self._analyze_security_issues())

        # Store suggestions in database
        for suggestion in suggestions:
            self._store_suggestion(suggestion)

        return suggestions

    def _analyze_code_duplication(self) -> List[ImprovementSuggestion]:
        """Analyze code for duplication patterns"""
        suggestions = []

        try:
            # Run duplicate code detection
            result = subprocess.run([
                'python', 'scripts/detect_duplication.py', '--detailed'
            ], capture_output=True, text=True, check=True)

            duplication_data = json.loads(result.stdout)

            for duplicate in duplication_data.get('duplicates', []):
                if duplicate['similarity'] > 0.8:  # High similarity threshold
                    suggestions.append(ImprovementSuggestion(
                        id=None,
                        title=f"Extract common code from {len(duplicate['files'])} files",
                        description=f"Found {duplicate['lines']} lines of duplicated code with {duplicate['similarity']:.1%} similarity",
                        category='code_quality',
                        priority='medium' if duplicate['lines'] > 20 else 'low',
                        estimated_effort='medium',
                        expected_impact='medium',
                        affected_files=duplicate['files'],
                        metrics_impact=['duplication_percentage'],
                        created_at=datetime.now(),
                        status='open'
                    ))

        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            pass  # Skip if duplication analysis fails

        return suggestions

    def _analyze_complexity_issues(self) -> List[ImprovementSuggestion]:
        """Analyze code complexity issues"""
        suggestions = []

        try:
            # Run complexity analysis
            result = subprocess.run([
                'radon', 'cc', 'tux', '--json', '--min', 'C'
            ], capture_output=True, text=True, check=True)

            complexity_data = json.loads(result.stdout)

            for file_path, functions in complexity_data.items():
                for func in functions:
                    if func['complexity'] > 15:  # High complexity threshold
                        suggestions.append(ImprovementSuggestion(
                            id=None,
                            title=f"Reduce complexity of {func['name']} function",
                            description=f"Function has complexity of {func['complexity']}, consider breaking it down into smaller functions",
                            category='code_quality',
                            priority='high' if func['complexity'] > 20 else 'medium',
                            estimated_effort='medium',
                            expected_impact='high',
                            affected_files=[file_path],
                            metrics_impact=['avg_complexity'],
                            created_at=datetime.now(),
                            status='open'
                        ))

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass  # Skip if complexity analysis fails

        return suggestions

    def _analyze_test_coverage_gaps(self) -> List[ImprovementSuggestion]:
        """Analyze test coverage gaps"""
        suggestions = []

        try:
            # Run coverage analysis
            result = subprocess.run([
                'coverage', 'json', '--pretty-print'
            ], capture_output=True, text=True, check=True)

            coverage_data = json.loads(result.stdout)

            for file_path, file_data in coverage_data['files'].items():
                if file_data['summary']['percent_covered'] < 80:  # Low coverage threshold
                    missing_lines = len(file_data['missing_lines'])

                    suggestions.append(ImprovementSuggestion(
                        id=None,
                        title=f"Improve test coverage for {os.path.basename(file_path)}",
                        description=f"File has {file_data['summary']['percent_covered']:.1f}% coverage with {missing_lines} uncovered lines",
                        category='testing',
                        priority='high' if file_data['summary']['percent_covered'] < 50 else 'medium',
                        estimated_effort='medium',
                        expected_impact='high',
                        affected_files=[file_path],
                        metrics_impact=['test_coverage'],
                        created_at=datetime.now(),
                        status='open'
                    ))

        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            pass  # Skip if coverage analysis fails

        return suggestions

    def _analyze_performance_opportunities(self) -> List[ImprovementSuggestion]:
        """Analyze performance improvement opportunities"""
        suggestions = []

        # Check for slow database queries
        slow_queries = self._identify_slow_queries()
        for query_info in slow_queries:
            suggestions.append(ImprovementSuggestion(
                id=None,
                title=f"Optimize slow database query in {query_info['file']}",
                description=f"Query takes {query_info['avg_time']:.2f}ms on average, consider adding indexes or optimizing",
                category='performance',
                priority='high' if query_info['avg_time'] > 1000 else 'medium',
                estimated_effort='medium',
                expected_impact='high',
                affected_files=[query_info['file']],
                metrics_impact=['avg_response_time', 'p95_response_time'],
                created_at=datetime.now(),
                status='open'
            ))

        # Check for memory usage patterns
        memory_issues = self._identify_memory_issues()
        for memory_info in memory_issues:
            suggestions.append(ImprovementSuggestion(
                id=None,
                title=f"Address memory usage in {memory_info['component']}",
                description=memory_info['description'],
                category='performance',
                priority=memory_info['priority'],
                estimated_effort='high',
                expected_impact='medium',
                affected_files=memory_info['files'],
                metrics_impact=['memory_usage'],
                created_at=datetime.now(),
                status='open'
            ))

        return suggestions

    def _analyze_security_issues(self) -> List[ImprovementSuggestion]:
        """Analyze security improvement opportunities"""
        suggestions = []

        try:
            # Run security analysis with bandit
            result = subprocess.run([
                'bandit', '-r', 'tux', '-f', 'json'
            ], capture_output=True, text=True)

            if result.stdout:
                security_data = json.loads(result.stdout)

                for issue in security_data.get('results', []):
                    if issue['issue_severity'] in ['HIGH', 'MEDIUM']:
                        suggestions.append(ImprovementSuggestion(
                            id=None,
                            title=f"Fix {issue['issue_severity'].lower()} security issue: {issue['test_name']}",
                            description=issue['issue_text'],
                            category='security',
                            priority='high' if issue['issue_severity'] == 'HIGH' else 'medium',
                            estimated_effort='low',
                            expected_impact='high',
                            affected_files=[issue['filename']],
                            metrics_impact=['security_score'],
                            created_at=datetime.now(),
                            status='open'
                        ))

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass  # Skip if security analysis fails

        return suggestions

    def _identify_slow_queries(self) -> List[Dict[str, Any]]:
        """Identify slow database queries (mock implementation)"""
        # In a real implementation, this would analyze query logs or use profiling
        return [
            {
                'file': 'tux/database/controllers/case.py',
                'query': 'SELECT * FROM cases WHERE guild_id = ?',
                'avg_time': 150.5,
                'call_count': 1250
            }
        ]

    def _identify_memory_issues(self) -> List[Dict[str, Any]]:
        """Identify memory usage issues (mock implementation)"""
        # In a real implementation, this would analyze memory profiling data
        return [
            {
                'component': 'Message Cache',
                'description': 'Message cache is growing unbounded, implement LRU eviction',
                'priority': 'medium',
                'files': ['tux/utils/cache.py']
            }
        ]

    def _store_suggestion(self, suggestion: ImprovementSuggestion):
        """Store suggestion in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO suggestions (
                    title, description, category, priority, estimated_effort,
                    expected_impact, affected_files, metrics_impact, created_at, status, assignee
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.title,
                suggestion.description,
                suggestion.category,
                suggestion.priority,
                suggestion.estimated_effort,
                suggestion.expected_impact,
                json.dumps(suggestion.affected_files),
                json.dumps(suggestion.metrics_impact),
                suggestion.created_at.isoformat(),
                suggestion.status,
                suggestion.assignee
            ))

    def collect_developer_feedback(self) -> List[FeedbackItem]:
        """Collect feedback from developers"""
        feedback_items = []

        # Check for feedback files
        feedback_dir = Path('feedback')
        if feedback_dir.exists():
            for feedback_file in feedback_dir.glob('*.json'):
                try:
                    with open(feedback_file, 'r') as f:
                        feedback_data = json.load(f)

                    feedback_item = FeedbackItem(
                        id=None,
                        source='developer',
                        feedback_type=feedback_data.get('type', 'suggestion'),
                        title=feedback_data['title'],
                        description=feedback_data['description'],
                        priority=feedback_data.get('priority', 3),
                        created_at=datetime.fromisoformat(feedback_data['created_at']),
                        status='open'
                    )

                    feedback_items.append(feedback_item)
                    self._store_feedback(feedback_item)

                    # Move processed feedback file
                    processed_dir = feedback_dir / 'processed'
                    processed_dir.mkdir(exist_ok=True)
                    feedback_file.rename(processed_dir / feedback_file.name)

                except (json.JSONDecodeError, KeyError):
                    continue

        return feedback_items

    def _store_feedback(self, feedback: FeedbackItem):
        """Store feedback in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback (
                    source, feedback_type, title, description, priority, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.source,
                feedback.feedback_type,
                feedback.title,
                feedback.description,
                feedback.priority,
                feedback.created_at.isoformat(),
                feedback.status
            ))

    def create_github_issues(self, suggestions: List[ImprovementSuggestion]) -> List[str]:
        """Create GitHub issues for high-priority suggestions"""
        if not self.github_token:
            print("GitHub token not available, skipping issue creation")
            return []

        created_issues = []

        # Filter high-priority suggestions
        high_priority_suggestions = [s for s in suggestions if s.priority == 'high']

        for suggestion in high_priority_suggestions[:5]:  # Limit to 5 issues per run
            issue_data = {
                'title': suggestion.title,
                'body': self._format_issue_body(suggestion),
                'labels': [
                    'improvement',
                    f'category:{suggestion.category}',
                    f'priority:{suggestion.priority}',
                    f'effort:{suggestion.estimated_effort}'
                ]
            }

            try:
                response = requests.post(
                    f'https://api.github.com/repos/{self.github_repo}/issues',
                    headers={
                        'Authorization': f'token {self.github_token}',
                        'Accept': 'application/vnd.github.v3+json'
                    },
                    json=issue_data
                )

                if response.status_code == 201:
                    issue_url = response.json()['html_url']
                    created_issues.append(issue_url)
                    print(f"Created issue: {issue_url}")

                    # Update suggestion status
                    self._update_suggestion_status(suggestion, 'in_progress')

            except requests.RequestException as e:
                print(f"Failed to create issue for {suggestion.title}: {e}")

        return created_issues

    def _format_issue_body(self, suggestion: ImprovementSuggestion) -> str:
        """Format GitHub issue body"""
        return f"""
## Description
{suggestion.description}

## Category
{suggestion.category.replace('_', ' ').title()}

## Priority
{suggestion.priority.title()}

## Estimated Effort
{suggestion.estimated_effort.title()}

## Expected Impact
{suggestion.expected_impact.title()}

## Affected Files
{chr(10).join(f'- {file}' for file in suggestion.affected_files)}

## Metrics Impact
This improvement is expected to impact the following metrics:
{chr(10).join(f'- {metric.replace("_", " ").title()}' for metric in suggestion.metrics_impact)}

## Acceptance Criteria
- [ ] Implementation completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Metrics show improvement

---
*This issue was automatically generated by the Continuous Improvement Pipeline*
"""

    def _update_suggestion_status(self, suggestion: ImprovementSuggestion, status: str):
        """Update suggestion status in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE suggestions
                SET status = ?
                WHERE title = ? AND created_at = ?
            """, (status, suggestion.title, suggestion.created_at.isoformat()))

    def detect_performance_regressions(self) -> List[Dict[str, Any]]:
        """Detect performance regressions"""
        regressions = []

        # Load current performance data
        perf_file = 'performance_results.json'
        if not os.path.exists(perf_file):
            return regressions

        try:
            with open(perf_file, 'r') as f:
                current_perf = json.load(f)
        except json.JSONDecodeError:
            return regressions

        # Compare with baselines
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM performance_baselines")
            baselines = {row[1]: row for row in cursor.fetchall()}  # operation_name -> row

        for operation, current_time in current_perf.items():
            if operation in baselines:
                baseline = baselines[operation]
                baseline_time = baseline[2]  # mean_time column

                # Check for regression (>20% slower)
                if current_time > baseline_time * 1.2:
                    regression_percent = ((current_time - baseline_time) / baseline_time) * 100

                    regressions.append({
                        'operation': operation,
                        'current_time': current_time,
                        'baseline_time': baseline_time,
                        'regression_percent': regression_percent,
                        'severity': 'high' if regression_percent > 50 else 'medium'
                    })

        return regressions

    def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate comprehensive improvement report"""
        with sqlite3.connect(self.db_path) as conn:
            # Get suggestion statistics
            cursor = conn.execute("""
                SELECT category, priority, status, COUNT(*) as count
                FROM suggestions
                GROUP BY category, priority, status
            """)
            suggestion_stats = cursor.fetchall()

            # Get feedback statistics
            cursor = conn.execute("""
                SELECT feedback_type, status, COUNT(*) as count
                FROM feedback
                GROUP BY feedback_type, status
            """)
            feedback_stats = cursor.fetchall()

            # Get recent suggestions
            cursor = conn.execute("""
                SELECT title, category, priority, created_at, status
                FROM suggestions
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT 10
            """, ((datetime.now() - timedelta(days=7)).isoformat(),))
            recent_suggestions = cursor.fetchall()

        return {
            'generated_at': datetime.now().isoformat(),
            'suggestion_statistics': suggestion_stats,
            'feedback_statistics': feedback_stats,
            'recent_suggestions': recent_suggestions,
            'total_open_suggestions': len([s for s in suggestion_stats if s[2] == 'open']),
            'high_priority_open': len([s for s in suggestion_stats if s[1] == 'high' and s[2] == 'open'])
        }

def main():
    """Main function to run the continuous improvement pipeline"""
    pipeline = ContinuousImprovementPipeline()

    print("Running Continuous Improvement Pipeline...")

    # Analyze codebase for improvements
    print("1. Analyzing codebase for improvements...")
    suggestions = pipeline.analyze_codebase_for_improvements()
    print(f"   Generated {len(suggestions)} improvement suggestions")

    # Collect developer feedback
    print("2. Collecting developer feedback...")
    feedback = pipeline.collect_developer_feedback()
    print(f"   Collected {len(feedback)} feedback items")

    # Detect performance regressions
    print("3. Detecting performance regressions...")
    regressions = pipeline.detect_performance_regressions()
    if regressions:
        print(f"   Found {len(regressions)} performance regressions")
        for regression in regressions:
            print(f"   - {regression['operation']}: {regression['regression_percent']:.1f}% slower")
    else:
        print("   No performance regressions detected")

    # Create GitHub issues for high-priority items
    print("4. Creating GitHub issues for high-priority suggestions...")
    created_issues = pipeline.create_github_issues(suggestions)
    print(f"   Created {len(created_issues)} GitHub issues")

    # Generate improvement report
    print("5. Generating improvement report...")
    report = pipeline.generate_improvement_report()

    with open('improvement_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("Continuous Improvement Pipeline completed successfully!")
    print(f"Report saved to improvement_report.json")

if __name__ == '__main__':
    main()
