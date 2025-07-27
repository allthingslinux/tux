#!/usr/bin/env python3
"""
Quality Gates Evaluator
Evaluates current metrics against defined quality gates
"""

import json
import sqlite3
import yaml
imp
om datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class QualityGate:
    name: str
    metric_name: str
    condition: str  # 'minimum_value', 'maximum_value', 'exact_value'
    threshold: float
    severity: str  # 'blocking', 'warning', 'info'
    description: str

@dataclass
class QualityGateResult:
    gate: QualityGate
    current_value: float
    passed: bool
    message: str

class QualityGateEvaluator:
    def __init__(self, config_path: str = "monitoring_config.yml", metrics_db_path: str = "metrics.db"):
        self.config_path = config_path
        self.metrics_db_path = metrics_db_path
        self.config = self._load_config()
        self.quality_gates = self._load_quality_gates()

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        if not os.path.exists(self.config_path):
            return {}

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_quality_gates(self) -> List[QualityGate]:
        """Load quality gates from configuration"""
        gates = []

        # Load deployment quality gates
        deployment_gates = self.config.get('quality_gates', {}).get('deployment', {}).get('required_metrics', [])

        for gate_config in deployment_gates:
            gate = QualityGate(
                name=f"deployment_{gate_config['name']}",
                metric_name=gate_config['name'],
                condition='minimum_value' if 'minimum_value' in gate_config else 'maximum_value',
                threshold=gate_config.get('minimum_value', gate_config.get('maximum_value', 0)),
                severity='blocking',
                description=f"Deployment gate for {gate_config['name']}"
            )
            gates.append(gate)

        # Add additional quality gates based on metric configuration
        metrics_config = self.config.get('metrics', {})

        for category, metrics in metrics_config.items():
            for metric_name, metric_config in metrics.items():
                # Create quality gate based on excellent threshold
                excellent_threshold = metric_config.get('excellent_threshold')
                if excellent_threshold is not None:
                    condition = 'minimum_value' if metric_config.get('trend_calculation') == 'higher_is_better' else 'maximum_value'

                    gate = QualityGate(
                        name=f"excellence_{metric_name}",
                        metric_name=metric_name,
                        condition=condition,
                        threshold=excellent_threshold,
                        severity='warning',
                        description=f"Excellence threshold for {metric_name}"
                    )
                    gates.append(gate)

        return gates

    def evaluate_all_gates(self) -> Dict[str, Any]:
        """Evaluate all quality gates"""
        results = []

        for gate in self.quality_gates:
            result = self._evaluate_gate(gate)
            results.append(result)

        # Calculate overall status
        blocking_failures = [r for r in results if not r.passed and r.gate.severity == 'blocking']
        warning_failures = [r for r in results if not r.passed and r.gate.severity == 'warning']

        overall_passed = len(blocking_failures) == 0

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_passed': overall_passed,
            'overall_status': self._calculate_overall_status(results),
            'total_gates': len(results),
            'passed_gates': len([r for r in results if r.passed]),
            'failed_gates': len([r for r in results if not r.passed]),
            'blocking_failures': len(blocking_failures),
            'warning_failures': len(warning_failures),
            'results': [self._result_to_dict(r) for r in results],
            'summary': self._generate_summary(results)
        }

    def _evaluate_gate(self, gate: QualityGate) -> QualityGateResult:
        """Evaluate a single quality gate"""
        current_value = self._get_current_metric_value(gate.metric_name)

        if current_value is None:
            return QualityGateResult(
                gate=gate,
                current_value=0.0,
                passed=False,
                message=f"Metric {gate.metric_name} not found"
            )

        # Evaluate condition
        if gate.condition == 'minimum_value':
            passed = current_value >= gate.threshold
            comparison = f"{current_value:.2f} >= {gate.threshold:.2f}"
        elif gate.condition == 'maximum_value':
            passed = current_value <= gate.threshold
            comparison = f"{current_value:.2f} <= {gate.threshold:.2f}"
        else:  # exact_value
            passed = abs(current_value - gate.threshold) < 0.01
            comparison = f"{current_value:.2f} == {gate.threshold:.2f}"

        message = f"{gate.description}: {comparison} - {'PASS' if passed else 'FAIL'}"

        return QualityGateResult(
            gate=gate,
            current_value=current_value,
            passed=passed,
            message=message
        )

    def _get_current_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for a metric"""
        if not os.path.exists(self.metrics_db_path):
            return None

        with sqlite3.connect(self.metrics_db_path) as conn:
            cursor = conn.execute("""
                SELECT value
                FROM metrics
                WHERE metric_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (metric_name,))

            row = cursor.fetchone()
            return row[0] if row else None

    def _calculate_overall_status(self, results: List[QualityGateResult]) -> str:
        """Calculate overall status based on results"""
        blocking_failures = [r for r in results if not r.passed and r.gate.severity == 'blocking']
        warning_failures = [r for r in results if not r.passed and r.gate.severity == 'warning']

        if blocking_failures:
            return 'failed'
        elif warning_failures:
            return 'warning'
        else:
            return 'passed'

    def _result_to_dict(self, result: QualityGateResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'gate_name': result.gate.name,
            'metric_name': result.gate.metric_name,
            'condition': result.gate.condition,
            'threshold': result.gate.threshold,
            'current_value': result.current_value,
            'passed': result.passed,
            'severity': result.gate.severity,
            'message': result.message
        }

    def _generate_summary(self, results: List[QualityGateResult]) -> Dict[str, Any]:
        """Generate summary of results"""
        by_severity = {}
        by_category = {}

        for result in results:
            # Group by severity
            severity = result.gate.severity
            if severity not in by_severity:
                by_severity[severity] = {'total': 0, 'passed': 0, 'failed': 0}

            by_severity[severity]['total'] += 1
            if result.passed:
                by_severity[severity]['passed'] += 1
            else:
                by_severity[severity]['failed'] += 1

            # Group by category (extract from gate name)
            category = result.gate.name.split('_')[0]
            if category not in by_category:
                by_category[category] = {'total': 0, 'passed': 0, 'failed': 0}

            by_category[category]['total'] += 1
            if result.passed:
                by_category[category]['passed'] += 1
            else:
                by_category[category]['failed'] += 1

        return {
            'by_severity': by_severity,
            'by_category': by_category,
            'critical_failures': [
                self._result_to_dict(r) for r in results
                if not r.passed and r.gate.severity == 'blocking'
            ],
            'recommendations': self._generate_recommendations(results)
        }

    def _generate_recommendations(self, results: List[QualityGateResult]) -> List[str]:
        """Generate recommendations based on failed gates"""
        recommendations = []

        failed_results = [r for r in results if not r.passed]

        for result in failed_results:
            metric_name = result.gate.metric_name

            if metric_name == 'test_coverage':
                recommendations.append(
                    f"Increase test coverage from {result.current_value:.1f}% to at least {result.gate.threshold:.1f}% by adding unit tests"
                )
            elif metric_name == 'error_rate':
                recommendations.append(
                    f"Reduce error rate from {result.current_value:.1f}% to below {result.gate.threshold:.1f}% by improving error handling"
                )
            elif metric_name == 'avg_response_time':
                recommendations.append(
                    f"Improve response time from {result.current_value:.1f}ms to below {result.gate.threshold:.1f}ms by optimizing performance"
                )
            elif metric_name == 'security_vulnerabilities':
                recommendations.append(
                    f"Fix {int(result.current_value)} security vulnerabilities to meet zero-vulnerability requirement"
                )
            else:
                recommendations.append(
                    f"Improve {metric_name} from {result.current_value:.2f} to meet threshold of {result.gate.threshold:.2f}"
                )

        return recommendations

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        report = f"""# Quality Gates Report

**Generated**: {results['timestamp']}
**Overall Status**: {results['overall_status'].upper()}
**Gates Passed**: {results['passed_gates']}/{results['total_gates']}

## Summary

"""

        if results['overall_passed']:
            report += "✅ **All quality gates passed!**\n\n"
        else:
            report += f"❌ **{results['failed_gates']} quality gates failed**\n\n"

            if results['blocking_failures'] > 0:
                report += f"🚨 **{results['blocking_failures']} blocking failures** - Deployment should be blocked\n\n"

            if results['warning_failures'] > 0:
                report += f"⚠️ **{results['warning_failures']} warnings** - Consider addressing before deployment\n\n"

        # Results by severity
        report += "## Results by Severity\n\n"
        for severity, stats in results['summary']['by_severity'].items():
            emoji = {'blocking': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, '📊')
            report += f"- {emoji} **{severity.title()}**: {stats['passed']}/{stats['total']} passed\n"

        # Failed gates details
        failed_gates = [r for r in results['results'] if not r['passed']]
        if failed_gates:
            report += "\n## Failed Gates\n\n"
            for gate in failed_gates:
                severity_emoji = {'blocking': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(gate['severity'], '📊')
                report += f"### {severity_emoji} {gate['gate_name']}\n"
                report += f"- **Metric**: {gate['metric_name']}\n"
                report += f"- **Current Value**: {gate['current_value']:.2f}\n"
                report += f"- **Threshold**: {gate['threshold']:.2f}\n"
                report += f"- **Condition**: {gate['condition'].replace('_', ' ').title()}\n"
                report += f"- **Message**: {gate['message']}\n\n"

        # Recommendations
        if results['summary']['recommendations']:
            report += "## Recommendations\n\n"
            for i, recommendation in enumerate(results['summary']['recommendations'], 1):
                report += f"{i}. {recommendation}\n"

        return report

def main():
    """Main function to evaluate quality gates"""
    evaluator = QualityGateEvaluator()

    print("Evaluating quality gates...")
    results = evaluator.evaluate_all_gates()

    # Save results
    with open('quality_gate_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Generate and save report
    report = evaluator.generate_report(results)
    with open('quality_gate_report.md', 'w') as f:
        f.write(report)

    # Print summary
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Gates Passed: {results['passed_gates']}/{results['total_gates']}")

    if results['blocking_failures'] > 0:
        print(f"🚨 {results['blocking_failures']} BLOCKING failures detected!")
        exit(1)
    elif results['warning_failures'] > 0:
        print(f"⚠️ {results['warning_failures']} warnings detected")
        exit(0)
    else:
        print("✅ All quality gates passed!")
        exit(0)

if __name__ == '__main__':
    main()
