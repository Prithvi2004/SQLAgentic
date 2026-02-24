"""
Reasoning Engine - Chain-of-Thought Analysis
Provides transparent step-by-step reasoning for query generation.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"
    ANALYTICAL = "ANALYTICAL"


@dataclass
class ReasoningStep:
    """Single step in reasoning chain"""
    step_number: int
    description: str
    action: str
    confidence: float  # 0.0 to 1.0


@dataclass
class QueryAnalysis:
    """Complete query analysis"""
    question: str
    complexity: QueryComplexity
    intent: str
    tables_needed: List[str]
    filters_needed: List[str]
    aggregations_needed: List[str]
    time_aspect: Optional[str]
    reasoning_steps: List[ReasoningStep]


class ReasoningEngine:
    """
    Analyzes user questions and provides chain-of-thought reasoning.
    Makes the AI's decision-making process transparent.
    """
    
    def __init__(self):
        """Initialize reasoning engine."""
        self.time_keywords = {
            'today': 'today',
            'yesterday': 'yesterday',
            'week': 'last 7 days',
            'month': 'last 30 days',
            'year': 'last 365 days',
            'latest': 'most recent',
            'recent': 'most recent'
        }
        
        self.aggregation_keywords = {
            'total': 'SUM',
            'sum': 'SUM',
            'count': 'COUNT',
            'average': 'AVG',
            'avg': 'AVG',
            'maximum': 'MAX',
            'max': 'MAX',
            'minimum': 'MIN',
            'min': 'MIN',
            'group': 'GROUP BY'
        }
    
    def analyze(self, question: str, schema_context: str = "") -> QueryAnalysis:
        """
        Analyze user question and create reasoning chain.
        
        Args:
            question: User's natural language question
            schema_context: Database schema information
            
        Returns:
            QueryAnalysis with complete reasoning
        """
        q_lower = question.lower()
        
        # Step 1: Determine complexity
        complexity = self._assess_complexity(q_lower)
        
        # Step 2: Detect intent
        intent = self._detect_intent(q_lower)
        
        # Step 3: Identify tables
        tables = self._identify_tables(q_lower, schema_context)
        
        # Step 4: Identify filters
        filters = self._identify_filters(q_lower)
        
        # Step 5: Identify aggregations
        aggregations = self._identify_aggregations(q_lower)
        
        # Step 6: Detect time aspect
        time_aspect = self._detect_time_aspect(q_lower)
        
        # Create reasoning steps
        reasoning_steps = self._create_reasoning_steps(
            question, complexity, tables, filters, aggregations, time_aspect
        )
        
        return QueryAnalysis(
            question=question,
            complexity=complexity,
            intent=intent,
            tables_needed=tables,
            filters_needed=filters,
            aggregations_needed=aggregations,
            time_aspect=time_aspect,
            reasoning_steps=reasoning_steps
        )
    
    def _assess_complexity(self, question: str) -> QueryComplexity:
        """Assess query complexity."""
        # Count complexity indicators
        indicators = 0
        
        if any(word in question for word in ['compare', 'versus', 'vs', 'difference']):
            indicators += 2
        
        if any(word in question for word in ['group', 'by', 'each', 'per']):
            indicators += 1
        
        if any(word in question for word in ['total', 'sum', 'average', 'count']):
            indicators += 1
        
        if any(word in question for word in ['trend', 'over time', 'change', 'growth']):
            indicators += 2
        
        if any(word in question for word in ['top', 'bottom', 'highest', 'lowest', 'best', 'worst']):
            indicators += 1
        
        # Determine complexity
        if indicators == 0:
            return QueryComplexity.SIMPLE
        elif indicators <= 2:
            return QueryComplexity.MODERATE
        elif indicators <= 4:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.ANALYTICAL
    
    def _detect_intent(self, question: str) -> str:
        """Detect user's intent."""
        if any(word in question for word in ['show', 'list', 'display', 'get', 'find']):
            return "Retrieve data"
        elif any(word in question for word in ['count', 'how many']):
            return "Count records"
        elif any(word in question for word in ['total', 'sum']):
            return "Calculate sum"
        elif any(word in question for word in ['average', 'avg', 'mean']):
            return "Calculate average"
        elif any(word in question for word in ['compare', 'difference']):
            return "Compare data"
        elif any(word in question for word in ['trend', 'over time']):
            return "Analyze trend"
        else:
            return "General query"
    
    def _identify_tables(self, question: str, schema_context: str) -> List[str]:
        """Identify required tables."""
        tables = []
        
        # Common table indicators
        if 'shipment' in question:
            tables.append('GV_SHIPMENT')
        if 'client' in question:
            tables.append('GV_CLIENT')
        if 'order' in question:
            tables.append('GV_ORDER')
        
        # If no tables found, try to extract from schema context
        if not tables and schema_context:
            # Simple extraction - could be improved
            if 'GV_SHIPMENT' in schema_context:
                tables.append('GV_SHIPMENT')
        
        return tables if tables else ['<unknown>']
    
    def _identify_filters(self, question: str) -> List[str]:
        """Identify required filters."""
        filters = []
        
        # Time filters
        time_filter = self._detect_time_aspect(question)
        if time_filter:
            filters.append(f"Time: {time_filter}")
        
        # Status filters
        if 'active' in question:
            filters.append("Status: Active")
        elif 'pending' in question:
            filters.append("Status: Pending")
        elif 'completed' in question:
            filters.append("Status: Completed")
        
        # Numeric filters
        if 'top' in question or 'bottom' in question:
            match = re.search(r'(top|bottom)\s+(\d+)', question)
            if match:
                filters.append(f"Limit: {match.group(1)} {match.group(2)}")
        
        return filters
    
    def _identify_aggregations(self, question: str) -> List[str]:
        """Identify required aggregations."""
        aggregations = []
        
        for keyword, agg_type in self.aggregation_keywords.items():
            if keyword in question:
                aggregations.append(agg_type)
        
        return list(set(aggregations))  # Remove duplicates
    
    def _detect_time_aspect(self, question: str) -> Optional[str]:
        """Detect time-related aspects."""
        for keyword, time_desc in self.time_keywords.items():
            if keyword in question:
                return time_desc
        return None
    
    def _create_reasoning_steps(
        self,
        question: str,
        complexity: QueryComplexity,
        tables: List[str],
        filters: List[str],
        aggregations: List[str],
        time_aspect: Optional[str]
    ) -> List[ReasoningStep]:
        """Create chain-of-thought reasoning steps."""
        steps = []
        step_num = 1
        
        # Step 1: Understand question
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Understand the question",
            action=f"Analyzing: '{question}'",
            confidence=0.95
        ))
        step_num += 1
        
        # Step 2: Assess complexity
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Assess complexity",
            action=f"Complexity level: {complexity.value}",
            confidence=0.90
        ))
        step_num += 1
        
        # Step 3: Identify tables
        if tables:
            steps.append(ReasoningStep(
                step_number=step_num,
                description="Identify required tables",
                action=f"Tables needed: {', '.join(tables)}",
                confidence=0.88
            ))
            step_num += 1
        
        # Step 4: Determine filters
        if filters or time_aspect:
            filter_desc = filters + ([f"Time: {time_aspect}"] if time_aspect else [])
            steps.append(ReasoningStep(
                step_number=step_num,
                description="Determine filters",
                action=f"Filters: {', '.join(filter_desc)}",
                confidence=0.85
            ))
            step_num += 1
        
        # Step 5: Plan aggregations
        if aggregations:
            steps.append(ReasoningStep(
                step_number=step_num,
                description="Plan aggregations",
                action=f"Aggregations: {', '.join(aggregations)}",
                confidence=0.82
            ))
            step_num += 1
        
        # Final step: Generate query
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Generate SQL query",
            action="Constructing optimized SQL",
            confidence=0.87
        ))
        
        return steps
    
    def format_reasoning_display(self, analysis: QueryAnalysis) -> str:
        """Format reasoning for display."""
        lines = []
        
        lines.append("\n🤔 CHAIN-OF-THOUGHT REASONING:")
        lines.append("=" * 80)
        lines.append(f"\nQuestion: {analysis.question}")
        lines.append(f"Complexity: {analysis.complexity.value}")
        lines.append(f"Intent: {analysis.intent}")
        
        if analysis.tables_needed:
            lines.append(f"Tables: {', '.join(analysis.tables_needed)}")
        
        lines.append("\nReasoning Steps:")
        for step in analysis.reasoning_steps:
            confidence_bar = "█" * int(step.confidence * 10)
            lines.append(f"  {step.step_number}. {step.description}")
            lines.append(f"     → {step.action}")
            lines.append(f"     Confidence: {confidence_bar} {step.confidence:.0%}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
