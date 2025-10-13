"""
Advanced Risk Assessment Engine
Comprehensive risk scoring and analysis for cyber insurance underwriting
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IndustryRiskProfile(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCIAL = "financial"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    GOVERNMENT = "government"
    OTHER = "other"

@dataclass
class RiskFactor:
    name: str
    score: float  # 0.0 to 1.0
    weight: float  # Importance multiplier
    explanation: str
    evidence: List[str]

@dataclass
class CoverageRecommendation:
    coverage_type: str
    recommended_limit: int
    minimum_limit: int
    reasoning: str
    risk_factors: List[str]

class CyberRiskAssessmentEngine:
    """
    Advanced cyber insurance risk assessment engine
    Analyzes multiple risk factors to generate comprehensive risk scores
    """
    
    def __init__(self):
        self.industry_risk_multipliers = {
            IndustryRiskProfile.HEALTHCARE: 0.95,
            IndustryRiskProfile.FINANCIAL: 0.90,
            IndustryRiskProfile.RETAIL: 0.75,
            IndustryRiskProfile.TECHNOLOGY: 0.80,
            IndustryRiskProfile.MANUFACTURING: 0.60,
            IndustryRiskProfile.EDUCATION: 0.70,
            IndustryRiskProfile.GOVERNMENT: 0.85,
            IndustryRiskProfile.OTHER: 0.65
        }
        
        self.employee_risk_bands = [
            (0, 10, 0.3),      # Very small
            (11, 50, 0.4),     # Small  
            (51, 200, 0.5),    # Medium
            (201, 1000, 0.7),  # Large
            (1001, 5000, 0.85), # Very large
            (5001, float('inf'), 0.95)  # Enterprise
        ]
        
        self.revenue_risk_bands = [
            (0, 1_000_000, 0.3),
            (1_000_001, 10_000_000, 0.5),
            (10_000_001, 50_000_000, 0.7),
            (50_000_001, 500_000_000, 0.85),
            (500_000_001, float('inf'), 0.95)
        ]

    def assess_comprehensive_risk(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive cyber risk assessment
        Returns detailed risk analysis with scores, factors, and recommendations
        """
        try:
            risk_factors = []
            
            # 1. Industry Risk Assessment
            industry_risk = self._assess_industry_risk(business_data)
            risk_factors.append(industry_risk)
            
            # 2. Company Size Risk Assessment
            size_risk = self._assess_company_size_risk(business_data)
            risk_factors.append(size_risk)
            
            # 3. Technology Risk Assessment
            tech_risk = self._assess_technology_risk(business_data)
            risk_factors.append(tech_risk)
            
            # 4. Data Sensitivity Risk Assessment
            data_risk = self._assess_data_sensitivity_risk(business_data)
            risk_factors.append(data_risk)
            
            # 5. Geographic Risk Assessment
            geo_risk = self._assess_geographic_risk(business_data)
            risk_factors.append(geo_risk)
            
            # 6. Financial Stability Risk Assessment
            financial_risk = self._assess_financial_risk(business_data)
            risk_factors.append(financial_risk)
            
            # Calculate overall risk score
            total_weighted_score = sum(factor.score * factor.weight for factor in risk_factors)
            total_weight = sum(factor.weight for factor in risk_factors)
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.5
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)
            
            # Generate coverage recommendations
            coverage_recommendations = self._generate_coverage_recommendations(
                overall_score, risk_factors, business_data
            )
            
            # Generate risk mitigation suggestions
            risk_mitigations = self._generate_risk_mitigations(risk_factors)
            
            return {
                "overall_risk_score": round(overall_score, 3),
                "risk_level": risk_level.value,
                "assessment_date": datetime.utcnow().isoformat(),
                "risk_factors": [
                    {
                        "name": factor.name,
                        "score": round(factor.score, 3),
                        "weight": factor.weight,
                        "explanation": factor.explanation,
                        "evidence": factor.evidence
                    }
                    for factor in risk_factors
                ],
                "coverage_recommendations": [
                    {
                        "coverage_type": rec.coverage_type,
                        "recommended_limit": rec.recommended_limit,
                        "minimum_limit": rec.minimum_limit,
                        "reasoning": rec.reasoning,
                        "risk_factors": rec.risk_factors
                    }
                    for rec in coverage_recommendations
                ],
                "risk_mitigation_suggestions": risk_mitigations,
                "assessment_confidence": self._calculate_confidence_score(business_data),
                "next_review_date": (datetime.utcnow() + timedelta(days=365)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive risk assessment: {str(e)}")
            return self._get_default_risk_assessment()

    def _assess_industry_risk(self, business_data: Dict[str, Any]) -> RiskFactor:
        """Assess risk based on industry type"""
        industry = str(business_data.get("industry_type", "")).lower()
        
        # Map industry to risk profile
        industry_mapping = {
            "healthcare": IndustryRiskProfile.HEALTHCARE,
            "health": IndustryRiskProfile.HEALTHCARE,
            "medical": IndustryRiskProfile.HEALTHCARE,
            "hospital": IndustryRiskProfile.HEALTHCARE,
            "finance": IndustryRiskProfile.FINANCIAL,
            "financial": IndustryRiskProfile.FINANCIAL,
            "bank": IndustryRiskProfile.FINANCIAL,
            "insurance": IndustryRiskProfile.FINANCIAL,
            "retail": IndustryRiskProfile.RETAIL,
            "ecommerce": IndustryRiskProfile.RETAIL,
            "shopping": IndustryRiskProfile.RETAIL,
            "technology": IndustryRiskProfile.TECHNOLOGY,
            "tech": IndustryRiskProfile.TECHNOLOGY,
            "software": IndustryRiskProfile.TECHNOLOGY,
            "it": IndustryRiskProfile.TECHNOLOGY,
            "manufacturing": IndustryRiskProfile.MANUFACTURING,
            "education": IndustryRiskProfile.EDUCATION,
            "school": IndustryRiskProfile.EDUCATION,
            "university": IndustryRiskProfile.EDUCATION,
            "government": IndustryRiskProfile.GOVERNMENT,
            "public": IndustryRiskProfile.GOVERNMENT
        }
        
        risk_profile = IndustryRiskProfile.OTHER
        for keyword, profile in industry_mapping.items():
            if keyword in industry:
                risk_profile = profile
                break
        
        risk_score = self.industry_risk_multipliers[risk_profile]
        
        evidence = [f"Industry identified as: {industry}"]
        if risk_profile != IndustryRiskProfile.OTHER:
            evidence.append(f"Mapped to risk profile: {risk_profile.value}")
        
        explanation = self._get_industry_risk_explanation(risk_profile)
        
        return RiskFactor(
            name="Industry Risk",
            score=risk_score,
            weight=0.25,  # 25% of total risk score
            explanation=explanation,
            evidence=evidence
        )

    def _assess_company_size_risk(self, business_data: Dict[str, Any]) -> RiskFactor:
        """Assess risk based on company size (employees and revenue)"""
        employees = int(business_data.get("total_employees", 0))
        revenue = float(business_data.get("total_revenues", 0))
        
        # Employee-based risk
        employee_risk = 0.5
        for min_emp, max_emp, risk in self.employee_risk_bands:
            if min_emp <= employees <= max_emp:
                employee_risk = risk
                break
        
        # Revenue-based risk
        revenue_risk = 0.5
        for min_rev, max_rev, risk in self.revenue_risk_bands:
            if min_rev <= revenue <= max_rev:
                revenue_risk = risk
                break
        
        # Combined size risk (weighted average)
        combined_risk = (employee_risk * 0.6) + (revenue_risk * 0.4)
        
        evidence = [
            f"Employee count: {employees:,}",
            f"Annual revenue: ${revenue:,.0f}"
        ]
        
        size_category = self._categorize_company_size(employees, revenue)
        explanation = f"Company size category: {size_category}. Larger companies face higher cyber risks due to increased attack surface and data volumes."
        
        return RiskFactor(
            name="Company Size Risk",
            score=combined_risk,
            weight=0.20,  # 20% of total risk score
            explanation=explanation,
            evidence=evidence
        )

    def _assess_technology_risk(self, business_data: Dict[str, Any]) -> RiskFactor:
        """Assess risk based on technology usage and digital footprint"""
        # Extract technology indicators from business description or industry
        business_desc = str(business_data.get("business_description", "")).lower()
        industry = str(business_data.get("industry_type", "")).lower()
        
        tech_indicators = {
            "cloud": 0.7,
            "saas": 0.75,
            "e-commerce": 0.8,
            "online": 0.7,
            "digital": 0.75,
            "mobile app": 0.8,
            "iot": 0.85,
            "ai": 0.8,
            "machine learning": 0.8,
            "blockchain": 0.75,
            "api": 0.7,
            "database": 0.7,
            "payment": 0.85,
            "credit card": 0.9,
            "customer data": 0.8,
            "remote work": 0.7,
            "vpn": 0.6,
            "website": 0.6
        }
        
        detected_tech = []
        tech_risk_scores = []
        
        for tech, risk_score in tech_indicators.items():
            if tech in business_desc or tech in industry:
                detected_tech.append(tech)
                tech_risk_scores.append(risk_score)
        
        # Calculate technology risk
        if tech_risk_scores:
            tech_risk = sum(tech_risk_scores) / len(tech_risk_scores)
            # Cap the risk to prevent over-scoring
            tech_risk = min(tech_risk, 0.95)
        else:
            tech_risk = 0.5  # Default if no tech indicators found
        
        evidence = []
        if detected_tech:
            evidence.append(f"Technology indicators found: {', '.join(detected_tech)}")
        else:
            evidence.append("No specific technology indicators detected")
        
        explanation = self._get_technology_risk_explanation(detected_tech)
        
        return RiskFactor(
            name="Technology Risk",
            score=tech_risk,
            weight=0.20,  # 20% of total risk score
            explanation=explanation,
            evidence=evidence
        )

    def _assess_data_sensitivity_risk(self, business_data: Dict[str, Any]) -> RiskFactor:
        """Assess risk based on types of sensitive data handled"""
        data_types = business_data.get("data_types", [])
        if isinstance(data_types, str):
            data_types = [data_types]
        
        business_desc = str(business_data.get("business_description", "")).lower()
        industry = str(business_data.get("industry_type", "")).lower()
        
        # Data sensitivity risk factors
        sensitive_data_indicators = {
            "pii": 0.8,
            "personally identifiable": 0.8,
            "phi": 0.95,
            "health": 0.9,
            "medical": 0.9,
            "payment": 0.9,
            "credit card": 0.95,
            "financial": 0.85,
            "ssn": 0.95,
            "social security": 0.95,
            "customer": 0.7,
            "employee": 0.7,
            "intellectual property": 0.75,
            "trade secret": 0.8,
            "proprietary": 0.75,
            "biometric": 0.9,
            "location": 0.7,
            "children": 0.9,
            "student": 0.8
        }
        
        detected_data_types = []
        data_risk_scores = []
        
        # Check data_types field
        for data_type in data_types:
            data_type_lower = str(data_type).lower()
            for indicator, risk_score in sensitive_data_indicators.items():
                if indicator in data_type_lower:
                    detected_data_types.append(indicator)
                    data_risk_scores.append(risk_score)
        
        # Check business description and industry
        combined_text = f"{business_desc} {industry}"
        for indicator, risk_score in sensitive_data_indicators.items():
            if indicator in combined_text and indicator not in detected_data_types:
                detected_data_types.append(indicator)
                data_risk_scores.append(risk_score)
        
        # Calculate data sensitivity risk
        if data_risk_scores:
            data_risk = max(data_risk_scores)  # Use highest risk data type
        else:
            data_risk = 0.5  # Default baseline risk
        
        evidence = []
        if detected_data_types:
            evidence.append(f"Sensitive data types identified: {', '.join(set(detected_data_types))}")
        else:
            evidence.append("No specific sensitive data indicators found")
        
        explanation = self._get_data_sensitivity_explanation(detected_data_types)
        
        return RiskFactor(
            name="Data Sensitivity Risk",
            score=data_risk,
            weight=0.15,  # 15% of total risk score
            explanation=explanation,
            evidence=evidence
        )

    def _assess_geographic_risk(self, business_data: Dict[str, Any]) -> RiskFactor:
        """Assess risk based on geographic location and regulatory environment"""
        states = [
            business_data.get("business_state", ""),
            business_data.get("mailing_state", "")
        ]
        
        # State-specific cyber risk factors
        state_risk_multipliers = {
            "CA": 0.8,  # CCPA requirements
            "NY": 0.85, # SHIELD Act
            "TX": 0.7,
            "FL": 0.7,
            "IL": 0.75,
            "MA": 0.8,  # Strong data protection laws
            "WA": 0.75,
            "VA": 0.7,
            "DC": 0.9,  # Government/federal presence
        }
        
        geographic_risks = []
        evidence = []
        
        for state in states:
            if state and state in state_risk_multipliers:
                risk_score = state_risk_multipliers[state]
                geographic_risks.append(risk_score)
                evidence.append(f"Operating in {state} (risk multiplier: {risk_score})")
        
        # Calculate geographic risk
        if geographic_risks:
            geo_risk = max(geographic_risks)
        else:
            geo_risk = 0.6  # Default if no state identified
            evidence.append("Geographic location not clearly identified")
        
        explanation = "Geographic risk considers state-specific cyber security regulations and threat landscapes."
        
        return RiskFactor(
            name="Geographic Risk",
            score=geo_risk,
            weight=0.10,  # 10% of total risk score
            explanation=explanation,
            evidence=evidence
        )

    def _assess_financial_risk(self, business_data: Dict[str, Any]) -> RiskFactor:
        """Assess financial stability and its impact on cyber security investment"""
        revenue = float(business_data.get("total_revenues", 0))
        assets = float(business_data.get("total_assets", 0))
        liabilities = float(business_data.get("total_liabilities", 0))
        
        # Financial stability indicators
        financial_risk = 0.5  # Default
        evidence = []
        
        # Revenue analysis
        if revenue > 0:
            evidence.append(f"Annual revenue: ${revenue:,.0f}")
            if revenue < 500_000:
                financial_risk += 0.2  # Higher risk for very small revenue
                evidence.append("Small revenue base may limit security investment")
            elif revenue > 100_000_000:
                financial_risk -= 0.1  # Lower risk for large revenue
                evidence.append("Large revenue base supports security investment")
        
        # Asset-liability ratio
        if assets > 0 and liabilities > 0:
            debt_ratio = liabilities / assets
            evidence.append(f"Debt-to-asset ratio: {debt_ratio:.2f}")
            if debt_ratio > 0.7:
                financial_risk += 0.15  # High debt may limit security spending
                evidence.append("High debt levels may constrain security spending")
            elif debt_ratio < 0.3:
                financial_risk -= 0.1  # Low debt indicates financial stability
                evidence.append("Low debt levels indicate financial stability")
        
        # Ensure risk stays within bounds
        financial_risk = max(0.1, min(0.9, financial_risk))
        
        explanation = "Financial stability affects ability to invest in cyber security measures and recover from incidents."
        
        return RiskFactor(
            name="Financial Risk",
            score=financial_risk,
            weight=0.10,  # 10% of total risk score
            explanation=explanation,
            evidence=evidence
        )

    def _determine_risk_level(self, overall_score: float) -> RiskLevel:
        """Convert numeric risk score to risk level enum"""
        if overall_score >= 0.85:
            return RiskLevel.CRITICAL
        elif overall_score >= 0.7:
            return RiskLevel.HIGH
        elif overall_score >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_coverage_recommendations(
        self, 
        overall_score: float, 
        risk_factors: List[RiskFactor], 
        business_data: Dict[str, Any]
    ) -> List[CoverageRecommendation]:
        """Generate coverage limit recommendations based on risk assessment"""
        
        revenue = float(business_data.get("total_revenues", 1_000_000))
        employees = int(business_data.get("total_employees", 10))
        
        # Base coverage calculation
        base_coverage = min(max(revenue * 0.1, 50_000), 10_000_000)
        
        # Adjust based on overall risk
        risk_multiplier = 1.0 + (overall_score * 0.5)  # 0% to 50% increase
        recommended_coverage = int(base_coverage * risk_multiplier)
        
        recommendations = []
        
        # Primary cyber liability coverage
        recommendations.append(CoverageRecommendation(
            coverage_type="Cyber Liability Aggregate",
            recommended_limit=recommended_coverage,
            minimum_limit=int(recommended_coverage * 0.5),
            reasoning=f"Based on revenue of ${revenue:,.0f} and risk score of {overall_score:.2f}",
            risk_factors=[factor.name for factor in risk_factors if factor.score > 0.7]
        ))
        
        # Business interruption coverage
        bi_coverage = int(recommended_coverage * 0.2)
        recommendations.append(CoverageRecommendation(
            coverage_type="Business Interruption",
            recommended_limit=bi_coverage,
            minimum_limit=int(bi_coverage * 0.5),
            reasoning="Cyber incidents can significantly disrupt business operations",
            risk_factors=["Technology Risk", "Company Size Risk"]
        ))
        
        # Cyber extortion coverage
        extortion_coverage = min(int(recommended_coverage * 0.1), 100_000)
        recommendations.append(CoverageRecommendation(
            coverage_type="Cyber Extortion",
            recommended_limit=extortion_coverage,
            minimum_limit=int(extortion_coverage * 0.5),
            reasoning="Ransomware attacks are increasingly common",
            risk_factors=["Technology Risk", "Data Sensitivity Risk"]
        ))
        
        return recommendations

    def _generate_risk_mitigations(self, risk_factors: List[RiskFactor]) -> List[Dict[str, str]]:
        """Generate risk mitigation recommendations"""
        mitigations = []
        
        for factor in risk_factors:
            if factor.score > 0.7:  # High risk factors
                mitigation = self._get_mitigation_for_factor(factor.name, factor.score)
                if mitigation:
                    mitigations.append(mitigation)
        
        # Add general recommendations
        mitigations.extend([
            {
                "category": "General Security",
                "recommendation": "Implement multi-factor authentication (MFA) for all user accounts",
                "priority": "high",
                "impact": "Reduces risk of account compromise by 99.9%"
            },
            {
                "category": "Employee Training",
                "recommendation": "Conduct regular cyber security awareness training",
                "priority": "medium",
                "impact": "Reduces human error risks and phishing susceptibility"
            },
            {
                "category": "Data Protection",
                "recommendation": "Implement data encryption at rest and in transit",
                "priority": "high",
                "impact": "Protects sensitive data even if systems are compromised"
            }
        ])
        
        return mitigations

    def _calculate_confidence_score(self, business_data: Dict[str, Any]) -> float:
        """Calculate confidence in the risk assessment based on data completeness"""
        key_fields = [
            "industry_type", "total_employees", "total_revenues",
            "business_description", "business_state", "data_types"
        ]
        
        completed_fields = sum(1 for field in key_fields if business_data.get(field))
        confidence = completed_fields / len(key_fields)
        
        return round(confidence, 2)

    def _get_default_risk_assessment(self) -> Dict[str, Any]:
        """Return default risk assessment when errors occur"""
        return {
            "overall_risk_score": 0.5,
            "risk_level": "medium",
            "assessment_date": datetime.utcnow().isoformat(),
            "risk_factors": [],
            "coverage_recommendations": [],
            "risk_mitigation_suggestions": [],
            "assessment_confidence": 0.0,
            "error": "Unable to complete full risk assessment",
            "next_review_date": (datetime.utcnow() + timedelta(days=365)).isoformat()
        }

    # Helper methods for explanations
    def _get_industry_risk_explanation(self, risk_profile: IndustryRiskProfile) -> str:
        explanations = {
            IndustryRiskProfile.HEALTHCARE: "Healthcare organizations face high cyber risks due to valuable PHI data and regulatory requirements (HIPAA).",
            IndustryRiskProfile.FINANCIAL: "Financial services are prime targets for cybercriminals due to direct access to funds and sensitive financial data.",
            IndustryRiskProfile.RETAIL: "Retail businesses face moderate-high risks due to payment card data and customer information.",
            IndustryRiskProfile.TECHNOLOGY: "Technology companies face high risks due to intellectual property and often being early adopters of new technologies.",
            IndustryRiskProfile.MANUFACTURING: "Manufacturing has moderate risks, increasing with IoT adoption and digitalization of operations.",
            IndustryRiskProfile.EDUCATION: "Educational institutions face moderate risks due to student data and often limited security resources.",
            IndustryRiskProfile.GOVERNMENT: "Government entities face high risks due to sensitive data and being high-value targets.",
            IndustryRiskProfile.OTHER: "General business risks apply without industry-specific threat factors."
        }
        return explanations.get(risk_profile, "Standard industry risk profile applies.")

    def _categorize_company_size(self, employees: int, revenue: float) -> str:
        if employees <= 10 and revenue <= 1_000_000:
            return "Micro Business"
        elif employees <= 50 and revenue <= 10_000_000:
            return "Small Business"
        elif employees <= 500 and revenue <= 50_000_000:
            return "Medium Business"
        elif employees <= 1000 and revenue <= 500_000_000:
            return "Large Business"
        else:
            return "Enterprise"

    def _get_technology_risk_explanation(self, detected_tech: List[str]) -> str:
        if not detected_tech:
            return "Standard technology risk profile with no specific high-risk technologies identified."
        
        high_risk_tech = ["payment", "credit card", "iot", "ai", "blockchain", "e-commerce"]
        high_risk_found = any(tech in detected_tech for tech in high_risk_tech)
        
        if high_risk_found:
            return f"Elevated technology risk due to use of: {', '.join(detected_tech)}. These technologies increase attack surface and data exposure."
        else:
            return f"Moderate technology risk with standard digital technologies: {', '.join(detected_tech)}."

    def _get_data_sensitivity_explanation(self, detected_data_types: List[str]) -> str:
        if not detected_data_types:
            return "Standard data sensitivity risk with no specific high-risk data types identified."
        
        critical_data = ["phi", "ssn", "credit card", "biometric"]
        critical_found = any(data in detected_data_types for data in critical_data)
        
        if critical_found:
            return f"High data sensitivity risk due to handling: {', '.join(set(detected_data_types))}. Critical data types require enhanced protection."
        else:
            return f"Moderate data sensitivity risk with standard sensitive data: {', '.join(set(detected_data_types))}."

    def _get_mitigation_for_factor(self, factor_name: str, score: float) -> Optional[Dict[str, str]]:
        """Get specific mitigation recommendation for high-risk factors"""
        mitigations = {
            "Industry Risk": {
                "category": "Industry Compliance",
                "recommendation": "Implement industry-specific security frameworks and compliance requirements",
                "priority": "critical" if score > 0.85 else "high",
                "impact": "Reduces regulatory and industry-specific cyber risks"
            },
            "Company Size Risk": {
                "category": "Enterprise Security",
                "recommendation": "Implement enterprise-grade security controls and dedicated security team",
                "priority": "high",
                "impact": "Scales security measures appropriate to company size and complexity"
            },
            "Technology Risk": {
                "category": "Technology Security",
                "recommendation": "Implement advanced threat detection and secure development practices",
                "priority": "high",
                "impact": "Protects against technology-specific vulnerabilities and threats"
            },
            "Data Sensitivity Risk": {
                "category": "Data Protection",
                "recommendation": "Implement data loss prevention (DLP) and advanced encryption",
                "priority": "critical" if score > 0.9 else "high",
                "impact": "Protects sensitive data from unauthorized access and breach"
            }
        }
        
        return mitigations.get(factor_name)

# Global instance
risk_assessment_engine = CyberRiskAssessmentEngine()