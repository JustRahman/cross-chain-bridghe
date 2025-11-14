"""Slippage protection calculator"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

from app.db.models.analytics import SlippageCalculation
from app.core.logging import log


class SlippageCalculator:
    """
    Calculate and analyze slippage for bridge transactions.

    Provides:
    - Estimated slippage percentage
    - Minimum received amount
    - Risk assessment
    - Protection recommendations
    """

    def __init__(self):
        self.max_safe_slippage = 1.0  # 1% is considered safe
        self.warning_slippage = 2.0  # 2% triggers warning
        self.critical_slippage = 5.0  # 5% is critical

    def calculate_slippage(
        self,
        bridge_name: str,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str,
        available_liquidity: Optional[str] = None
    ) -> Dict:
        """
        Calculate slippage for a bridge transaction.

        Args:
            bridge_name: Bridge protocol name
            source_chain: Source blockchain
            destination_chain: Destination blockchain
            token: Token being bridged
            amount: Amount in smallest unit
            available_liquidity: Available liquidity if known

        Returns:
            Dict with slippage analysis
        """
        try:
            amount_decimal = Decimal(amount)

            # Base slippage (0.05% for small transactions)
            base_slippage = Decimal("0.05")

            # Calculate liquidity-based slippage
            liquidity_slippage = Decimal("0")
            liquidity_utilization = 0.0

            if available_liquidity:
                liquidity_decimal = Decimal(available_liquidity)

                if liquidity_decimal > 0:
                    # Calculate what percentage of liquidity this transaction uses
                    liquidity_utilization = float((amount_decimal / liquidity_decimal) * 100)

                    # Slippage increases with liquidity utilization
                    if liquidity_utilization > 80:
                        liquidity_slippage = Decimal("5.0")  # 5% for very high utilization
                    elif liquidity_utilization > 50:
                        liquidity_slippage = Decimal("2.0")  # 2% for high utilization
                    elif liquidity_utilization > 20:
                        liquidity_slippage = Decimal("1.0")  # 1% for medium utilization
                    elif liquidity_utilization > 10:
                        liquidity_slippage = Decimal("0.5")  # 0.5% for low-medium utilization
                    else:
                        liquidity_slippage = Decimal("0.1")  # 0.1% for low utilization

            # Bridge-specific slippage factors
            bridge_factors = {
                "across": Decimal("0.05"),
                "stargate": Decimal("0.1"),
                "hop": Decimal("0.15"),
                "connext": Decimal("0.2"),
                "celer": Decimal("0.05"),
                "orbiter": Decimal("0.05"),
                "debridge": Decimal("0.15"),
                "layerzero": Decimal("0.1"),
                "wormhole": Decimal("0.2"),
                "synapse": Decimal("0.15")
            }

            bridge_slippage = bridge_factors.get(bridge_name.lower(), Decimal("0.2"))

            # Total estimated slippage
            total_slippage = base_slippage + liquidity_slippage + bridge_slippage

            # Calculate minimum received amount
            slippage_multiplier = (Decimal("100") - total_slippage) / Decimal("100")
            min_received = str(int(amount_decimal * slippage_multiplier))

            # Assess risk level
            risk_level = self._assess_risk_level(float(total_slippage))

            # Generate warnings
            warnings = self._generate_warnings(
                float(total_slippage),
                liquidity_utilization,
                amount_decimal
            )

            # Recommendations
            recommendation = self._get_recommendation(risk_level, float(total_slippage))

            result = {
                "estimated_slippage_percent": float(total_slippage),
                "min_received_amount": min_received,
                "max_slippage_percent": 2.0,  # Default max tolerated
                "risk_level": risk_level,
                "warnings": warnings,
                "recommendation": recommendation,
                "liquidity_utilization": liquidity_utilization,
                "breakdown": {
                    "base_slippage": float(base_slippage),
                    "liquidity_impact": float(liquidity_slippage),
                    "bridge_factor": float(bridge_slippage)
                }
            }

            return result

        except Exception as e:
            log.error(f"Error calculating slippage: {str(e)}")
            # Return safe defaults
            return {
                "estimated_slippage_percent": 1.0,
                "min_received_amount": str(int(Decimal(amount) * Decimal("0.99"))),
                "max_slippage_percent": 2.0,
                "risk_level": "medium",
                "warnings": ["Unable to calculate accurate slippage"],
                "recommendation": "Proceed with caution",
                "liquidity_utilization": 0.0,
                "breakdown": {
                    "base_slippage": 0.5,
                    "liquidity_impact": 0.3,
                    "bridge_factor": 0.2
                }
            }

    def _assess_risk_level(self, slippage: float) -> str:
        """Assess risk level based on slippage"""
        if slippage < self.max_safe_slippage:
            return "low"
        elif slippage < self.warning_slippage:
            return "medium"
        elif slippage < self.critical_slippage:
            return "high"
        else:
            return "critical"

    def _generate_warnings(
        self,
        slippage: float,
        liquidity_utilization: float,
        amount: Decimal
    ) -> List[str]:
        """Generate warnings based on slippage analysis"""
        warnings = []

        if slippage > self.critical_slippage:
            warnings.append(f"CRITICAL: Slippage of {slippage:.2f}% is extremely high")
            warnings.append("Consider splitting into smaller transactions")

        elif slippage > self.warning_slippage:
            warnings.append(f"WARNING: Slippage of {slippage:.2f}% is above recommended threshold")

        if liquidity_utilization > 80:
            warnings.append("CRITICAL: This transaction uses >80% of available liquidity")
            warnings.append("High risk of transaction failure or extreme slippage")

        elif liquidity_utilization > 50:
            warnings.append("WARNING: This transaction uses >50% of available liquidity")

        if amount > Decimal("10000000000"):  # > 10,000 USDC
            warnings.append("Large transaction amount - consider splitting for better execution")

        if not warnings:
            warnings.append("Transaction parameters are within safe ranges")

        return warnings

    def _get_recommendation(self, risk_level: str, slippage: float) -> str:
        """Get recommendation based on risk level"""
        if risk_level == "critical":
            return f"DO NOT PROCEED - Slippage of {slippage:.2f}% is unacceptably high. Split transaction or wait for better liquidity."

        elif risk_level == "high":
            return f"HIGH RISK - Slippage of {slippage:.2f}% may result in significant losses. Consider alternative routes or smaller amounts."

        elif risk_level == "medium":
            return f"PROCEED WITH CAUTION - Slippage of {slippage:.2f}% is above ideal but acceptable. Review transaction details carefully."

        else:
            return f"SAFE TO PROCEED - Slippage of {slippage:.2f}% is within acceptable ranges."

    def calculate_protection_parameters(
        self,
        amount: str,
        max_slippage_tolerance: float = 2.0
    ) -> Dict:
        """
        Calculate protection parameters for transaction.

        Args:
            amount: Transaction amount
            max_slippage_tolerance: Maximum acceptable slippage %

        Returns:
            Protection parameters for transaction execution
        """
        amount_decimal = Decimal(amount)
        tolerance_decimal = Decimal(str(max_slippage_tolerance))

        # Minimum amount out (amount - max slippage)
        min_amount_out = amount_decimal * (Decimal("100") - tolerance_decimal) / Decimal("100")

        # Deadline (15 minutes from now)
        deadline = int(datetime.utcnow().timestamp()) + 900

        return {
            "min_amount_out": str(int(min_amount_out)),
            "max_slippage_bps": int(tolerance_decimal * 100),  # Convert to basis points
            "deadline": deadline,
            "amount_in": amount,
            "protection_enabled": True
        }

    def analyze_historical_slippage(
        self,
        bridge_name: str,
        source_chain: str,
        destination_chain: str,
        db_session
    ) -> Dict:
        """
        Analyze historical slippage for a specific route.

        Args:
            bridge_name: Bridge protocol
            source_chain: Source blockchain
            destination_chain: Destination blockchain
            db_session: Database session

        Returns:
            Historical slippage analysis
        """
        try:
            from datetime import timedelta

            # Get last 24 hours of slippage calculations
            cutoff = datetime.utcnow() - timedelta(hours=24)

            calculations = db_session.query(SlippageCalculation).filter(
                SlippageCalculation.bridge_name == bridge_name,
                SlippageCalculation.source_chain == source_chain,
                SlippageCalculation.destination_chain == destination_chain,
                SlippageCalculation.calculated_at >= cutoff
            ).all()

            if not calculations:
                return {
                    "average_slippage": 0.5,
                    "max_slippage": 1.0,
                    "min_slippage": 0.1,
                    "sample_size": 0,
                    "period_hours": 24
                }

            slippages = [c.estimated_slippage_percent for c in calculations]

            return {
                "average_slippage": sum(slippages) / len(slippages),
                "max_slippage": max(slippages),
                "min_slippage": min(slippages),
                "sample_size": len(calculations),
                "period_hours": 24
            }

        except Exception as e:
            log.error(f"Error analyzing historical slippage: {str(e)}")
            return {
                "average_slippage": 0.5,
                "max_slippage": 1.0,
                "min_slippage": 0.1,
                "sample_size": 0,
                "period_hours": 24
            }


# Global instance
slippage_calculator = SlippageCalculator()
