"""
SQL Safety Validator - Enhanced Security Layer
Prevents SQL injection and dangerous operations through parsing and validation.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of SQL validation"""
    is_safe: bool
    severity: str  # 'safe', 'warning', 'critical'
    issues: List[str]
    suggestions: List[str]
    score: int  # 0-100


class SQLSafetyValidator:
    """
    Enhanced SQL safety validation with parsing and pattern detection.
    Prevents SQL injection and enforces read-only operations.
    """
    
    def __init__(self, allow_modifications: bool = False):
        """
        Initialize validator.
        
        Args:
            allow_modifications: If True, allow INSERT/UPDATE/DELETE operations
        """
        self.allow_modifications = allow_modifications
        
        # Dangerous operations (blocked by default)
        self.dangerous_operations = {
            'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE',
            'EXEC', 'EXECUTE', 'sp_', 'xp_', 'BACKUP', 'RESTORE'
        }
        
        # Modification operations (blocked unless allow_modifications=True)
        self.modification_operations = {'INSERT', 'UPDATE', 'DELETE', 'MERGE'}
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r';\s*DROP',  # SQL injection attempt
            r'--',  # SQL comments (potential injection)
            r'/\*.*\*/',  # Block comments
            r'UNION\s+SELECT',  # Union-based injection
            r'OR\s+1\s*=\s*1',  # Always-true conditions
            r'OR\s+\'1\'\s*=\s*\'1\'',  # Always-true string conditions
            r'WAITFOR\s+DELAY',  # Time-based attacks
            r'BENCHMARK\s*\(',  # MySQL benchmark attacks
            r'SLEEP\s*\(',  # Sleep-based attacks
            r'INTO\s+OUTFILE',  # File writing
            r'LOAD_FILE\s*\(',  # File reading
        ]
    
    def validate(self, sql: str) -> ValidationResult:
        """
        Comprehensive SQL validation.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            ValidationResult with safety assessment
        """
        issues = []
        suggestions = []
        severity = 'safe'
        score = 100
        
        # Normalize SQL
        sql_upper = sql.upper().strip()
        
        # Check 1: Dangerous operations
        dangerous_found = self._check_dangerous_operations(sql_upper)
        if dangerous_found:
            issues.append(f"Dangerous operation detected: {', '.join(dangerous_found)}")
            severity = 'critical'
            score = 0
            return ValidationResult(False, severity, issues, suggestions, score)
        
        # Check 2: Modification operations
        if not self.allow_modifications:
            mod_found = self._check_modification_operations(sql_upper)
            if mod_found:
                issues.append(f"Modification operation not allowed: {', '.join(mod_found)}")
                severity = 'critical'
                score = 0
                return ValidationResult(False, severity, issues, suggestions, score)
        
        # Check 3: Suspicious patterns
        suspicious_found = self._check_suspicious_patterns(sql)
        if suspicious_found:
            issues.extend(suspicious_found)
            severity = 'critical'
            score = 0
            return ValidationResult(False, severity, issues, suggestions, score)
        
        # Check 4: SQL injection patterns
        injection_risk = self._check_injection_risk(sql)
        if injection_risk:
            issues.extend(injection_risk)
            severity = 'warning'
            score -= len(injection_risk) * 20
        
        # Check 5: Best practices
        warnings = self._check_best_practices(sql_upper)
        if warnings:
            suggestions.extend(warnings)
            if severity == 'safe':
                severity = 'warning'
            score -= len(warnings) * 10
        
        # Ensure score is in valid range
        score = max(0, min(100, score))
        
        is_safe = severity != 'critical' and score >= 50
        
        return ValidationResult(is_safe, severity, issues, suggestions, score)
    
    def _check_dangerous_operations(self, sql_upper: str) -> List[str]:
        """Check for dangerous SQL operations."""
        found = []
        for operation in self.dangerous_operations:
            if re.search(r'\b' + operation + r'\b', sql_upper):
                found.append(operation)
        return found
    
    def _check_modification_operations(self, sql_upper: str) -> List[str]:
        """Check for data modification operations."""
        found = []
        for operation in self.modification_operations:
            if re.search(r'\b' + operation + r'\b', sql_upper):
                found.append(operation)
        return found
    
    def _check_suspicious_patterns(self, sql: str) -> List[str]:
        """Check for suspicious SQL patterns."""
        found = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                found.append(f"Suspicious pattern detected: {pattern}")
        return found
    
    def _check_injection_risk(self, sql: str) -> List[str]:
        """Check for SQL injection risk indicators."""
        risks = []
        
        # Check for unescaped quotes
        if "'" in sql and not self._is_properly_escaped(sql):
            risks.append("Potential SQL injection: unescaped quotes detected")
        
        # Check for dynamic SQL construction indicators
        if '+' in sql or '||' in sql:
            risks.append("Potential SQL injection: string concatenation detected")
        
        return risks
    
    def _is_properly_escaped(self, sql: str) -> bool:
        """Check if quotes are properly escaped."""
        # Simple check: look for '' (escaped single quote)
        # This is a basic check and could be improved
        return "''" in sql or "\\'" in sql
    
    def _check_best_practices(self, sql_upper: str) -> List[str]:
        """Check for SQL best practices."""
        suggestions = []
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*', sql_upper):
            suggestions.append("Consider specifying column names instead of SELECT *")
        
        # Check for missing WHERE clause in UPDATE/DELETE
        if 'UPDATE' in sql_upper and 'WHERE' not in sql_upper:
            suggestions.append("UPDATE without WHERE clause will affect all rows")
        
        if 'DELETE' in sql_upper and 'WHERE' not in sql_upper:
            suggestions.append("DELETE without WHERE clause will remove all rows")
        
        # Check for missing TOP/LIMIT
        if 'SELECT' in sql_upper and 'TOP' not in sql_upper and 'LIMIT' not in sql_upper:
            if 'WHERE' not in sql_upper:
                suggestions.append("Consider adding TOP N or LIMIT to prevent large result sets")
        
        return suggestions
    
    def format_validation_report(self, result: ValidationResult) -> str:
        """Format validation result for display."""
        lines = []
        
        # Header with score
        if result.severity == 'critical':
            icon = "🚨"
            status = "BLOCKED"
        elif result.severity == 'warning':
            icon = "⚠️"
            status = "WARNING"
        else:
            icon = "✅"
            status = "SAFE"
        
        lines.append(f"\n{icon} SQL SAFETY CHECK: {status} (Score: {result.score}/100)")
        lines.append("=" * 80)
        
        # Issues
        if result.issues:
            lines.append("\n🚫 Security Issues:")
            for issue in result.issues:
                lines.append(f"   • {issue}")
        
        # Suggestions
        if result.suggestions:
            lines.append("\n💡 Suggestions:")
            for suggestion in result.suggestions:
                lines.append(f"   • {suggestion}")
        
        if result.is_safe:
            lines.append("\n✅ Query is safe to execute")
        else:
            lines.append("\n❌ Query blocked for security reasons")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


class SafetyViolationError(Exception):
    """Raised when SQL query violates safety rules."""
    pass
