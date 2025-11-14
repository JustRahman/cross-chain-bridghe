"""Route endpoints for quote and execution"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import uuid

from app.db.base import get_db
from app.schemas.route import (
    RouteQuoteRequest,
    RouteQuoteResponse,
    RouteExecuteRequest,
    RouteExecuteResponse,
    TransactionStatus,
    RouteOption,
    CostBreakdown,
    TransactionData,
    BatchQuoteRequest,
    BatchQuoteResponse,
    BatchQuoteResult
)
from app.models.transaction import Transaction
from app.core.security import get_api_key
from app.core.logging import log
from app.services.route_discovery import route_discovery_engine
from app.services.bridges.base import RouteParams
from app.services.timeout_estimator import timeout_estimator
from decimal import Decimal


router = APIRouter()


@router.post("/quote", response_model=RouteQuoteResponse)
async def get_route_quote(
    request: RouteQuoteRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get route quotes for a cross-chain transfer.

    This endpoint queries multiple bridge protocols and DEX aggregators
    to find the best routes for transferring assets between chains.

    Returns a list of route options sorted by total cost (lowest first).
    """
    try:
        log.info(
            f"Route quote requested: {request.source_chain} -> {request.destination_chain}"
        )

        # Create route parameters
        route_params = RouteParams(
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            source_token=request.source_token,
            destination_token=request.destination_token,
            amount=request.amount,
            user_address=request.user_address
        )

        # Discover routes using route discovery engine
        bridge_quotes = await route_discovery_engine.discover_routes(route_params)

        if not bridge_quotes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No routes found for {request.source_chain} -> {request.destination_chain}"
            )

        # Convert BridgeQuote objects to RouteOption schema
        routes = []
        for bridge_quote in bridge_quotes:
            route_option = RouteOption(
                bridge_name=bridge_quote.bridge_name,
                route_type=bridge_quote.route_type,
                estimated_time_seconds=bridge_quote.estimated_time_seconds,
                cost_breakdown=CostBreakdown(
                    bridge_fee_usd=float(bridge_quote.fee_breakdown.bridge_fee_usd),
                    gas_cost_source_usd=float(bridge_quote.fee_breakdown.gas_cost_source_usd),
                    gas_cost_destination_usd=float(bridge_quote.fee_breakdown.gas_cost_destination_usd),
                    total_cost_usd=float(bridge_quote.fee_breakdown.total_cost_usd),
                    slippage_percentage=float(bridge_quote.fee_breakdown.slippage_percentage) if bridge_quote.fee_breakdown.slippage_percentage else None
                ),
                success_rate=float(bridge_quote.success_rate),
                steps=bridge_quote.steps,
                requires_approval=bridge_quote.requires_approval,
                minimum_amount=bridge_quote.minimum_amount,
                maximum_amount=bridge_quote.maximum_amount
            )
            routes.append(route_option)

        # Generate quote ID
        quote_id = f"quote_{uuid.uuid4().hex[:16]}"

        # Create response
        response = RouteQuoteResponse(
            routes=routes,
            quote_id=quote_id,
            expires_at=int(datetime.utcnow().timestamp()) + 300  # 5 minutes
        )

        log.info(f"Returning {len(routes)} route options")
        return response

    except Exception as e:
        log.error(f"Error getting route quote: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get route quote: {str(e)}"
        )


@router.post("/execute", response_model=RouteExecuteResponse)
async def execute_route(
    request: RouteExecuteRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Execute a route by generating unsigned transaction data.

    Returns transaction data that the user needs to sign and submit
    with their wallet. Also creates a transaction record for monitoring.
    """
    try:
        log.info(f"Route execution requested for quote: {request.quote_id}")

        # TODO: Implement actual transaction generation
        # For now, return mock data

        # Create transaction record
        transaction_id = f"tx_{uuid.uuid4().hex[:16]}"

        # Hash user address for privacy
        user_address_hash = hashlib.sha256(request.user_address.encode()).hexdigest()

        # Create transaction in database
        transaction = Transaction(
            api_key_id=1,  # TODO: Get actual API key ID
            source_chain="ethereum",
            destination_chain="arbitrum",
            source_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            destination_token="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            amount="1000000000",
            bridge_name="Across Protocol",
            status="pending",
            user_address_hash=user_address_hash,
            estimated_time_seconds=180
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Mock transaction data
        transactions = [
            TransactionData(
                to="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                data="0x095ea7b3000000000000000000000000000000000000000000000000000000003b9aca00",
                value="0",
                gas_limit="50000",
                chain_id=1
            ),
            TransactionData(
                to="0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5",
                data="0xabcdef123456...",
                value="0",
                gas_limit="200000",
                chain_id=1
            )
        ]

        response = RouteExecuteResponse(
            transaction_id=transaction_id,
            transactions=transactions,
            estimated_completion_time=180,
            status_url=f"/api/v1/routes/status/{transaction_id}"
        )

        return response

    except Exception as e:
        log.error(f"Error executing route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute route: {str(e)}"
        )


@router.get("/status/{transaction_id}", response_model=TransactionStatus)
async def get_transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get the status of a cross-chain transfer.

    Returns current status, transaction hashes, and progress information.
    """
    try:
        # TODO: Query actual transaction from database
        # For now, return mock status

        status_response = TransactionStatus(
            transaction_id=transaction_id,
            status="processing",
            source_tx_hash="0xabc123def456...",
            destination_tx_hash=None,
            progress=50,
            message="Bridge transfer in progress",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )

        return status_response

    except Exception as e:
        log.error(f"Error getting transaction status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction status: {str(e)}"
        )


@router.post("/batch-quote", response_model=BatchQuoteResponse)
async def get_batch_quotes(
    batch_request: BatchQuoteRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get quotes for multiple routes in a single API call.

    Efficiently process up to 10 quote requests simultaneously.
    Useful for:
    - Comparing multiple routes at once
    - Pre-fetching quotes for UI selection
    - Batch operations

    Each quote in the batch is processed independently - if one fails,
    others will still succeed.
    """
    import time
    import asyncio

    start_time = time.time()

    try:
        results = []
        tasks = []

        # Create tasks for all quotes
        for index, quote_request in enumerate(batch_request.quotes):
            async def process_quote(idx, req):
                try:
                    # Convert to route params
                    params = RouteParams(
                        source_chain=req.source_chain,
                        destination_chain=req.destination_chain,
                        source_token=req.source_token,
                        destination_token=req.destination_token,
                        amount=req.amount,
                        user_address=req.user_address
                    )

                    # Get routes
                    routes = await route_discovery_engine.discover_routes(params)

                    # Generate quote ID
                    quote_content = f"{req.source_chain}{req.destination_chain}{req.amount}{datetime.utcnow().timestamp()}{idx}"
                    quote_id = f"quote_{hashlib.md5(quote_content.encode()).hexdigest()[:12]}"

                    # Calculate expiry (15 minutes from now)
                    expires_at = int((datetime.utcnow().timestamp() + 900))

                    # Build quote response
                    route_options = []
                    for route in routes:
                        route_option = RouteOption(
                            bridge_name=route.bridge_name,
                            route_type=route.route_type,
                            estimated_time_seconds=route.estimated_time_seconds,
                            cost_breakdown=CostBreakdown(
                                bridge_fee_usd=float(route.fee_breakdown.bridge_fee_usd),
                                gas_cost_source_usd=float(route.fee_breakdown.gas_cost_source_usd),
                                gas_cost_destination_usd=float(route.fee_breakdown.gas_cost_destination_usd),
                                total_cost_usd=float(route.fee_breakdown.total_cost_usd),
                                slippage_percentage=float(route.fee_breakdown.slippage_percentage) if route.fee_breakdown.slippage_percentage else None
                            ),
                            success_rate=float(route.success_rate),
                            steps=route.steps,
                            requires_approval=route.requires_approval,
                            minimum_amount=route.minimum_amount,
                            maximum_amount=route.maximum_amount
                        )
                        route_options.append(route_option)

                    quote_response = RouteQuoteResponse(
                        routes=route_options,
                        quote_id=quote_id,
                        expires_at=expires_at
                    )

                    return BatchQuoteResult(
                        request_index=idx,
                        success=True,
                        quote=quote_response,
                        error=None
                    )

                except Exception as e:
                    log.error(f"Error processing batch quote {idx}: {str(e)}")
                    return BatchQuoteResult(
                        request_index=idx,
                        success=False,
                        quote=None,
                        error=str(e)
                    )

            tasks.append(process_quote(index, quote_request))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        # Calculate metrics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        processing_time_ms = int((time.time() - start_time) * 1000)

        log.info(f"Batch quote completed: {successful}/{len(results)} successful in {processing_time_ms}ms")

        return BatchQuoteResponse(
            results=results,
            total_requests=len(batch_request.quotes),
            successful=successful,
            failed=failed,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        log.error(f"Error processing batch quotes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch quotes: {str(e)}"
        )


@router.post("/multi-hop")
async def get_multi_hop_routes(
    source_chain: str,
    destination_chain: str,
    token: str,
    amount: str,
    max_hops: int = 2,
    include_direct: bool = True,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Find optimal routes including multi-hop paths.

    This advanced endpoint analyzes both direct and multi-hop routes
    to find the most cost-effective path for your transfer.

    Multi-hop routes go through intermediate chains:
    - Example: Ethereum → Polygon → Arbitrum
    - Can be cheaper than direct routes
    - Takes longer but saves on fees

    Query Parameters:
    - max_hops: Maximum hops (1-3, default: 2)
    - include_direct: Whether to compare with direct routes (default: true)

    Returns:
    - Best route (direct or multi-hop)
    - Alternative routes
    - Savings comparison
    """
    try:
        from app.services.multi_hop_router import multi_hop_router

        # Validate max_hops
        if max_hops < 1 or max_hops > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_hops must be between 1 and 3"
            )

        log.info(
            f"Multi-hop route search: {source_chain} -> {destination_chain}, "
            f"token: {token}, amount: {amount}, max_hops: {max_hops}"
        )

        # Find best route
        result = await multi_hop_router.find_best_route(
            source_chain=source_chain,
            destination_chain=destination_chain,
            token=token,
            amount=amount,
            max_hops=max_hops,
            include_multi_hop=(max_hops > 1)
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error finding multi-hop routes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find multi-hop routes: {str(e)}"
        )


@router.get("/timeout-estimate")
async def estimate_transaction_timeout(
    bridge_name: str,
    source_chain: str,
    destination_chain: str,
    amount_usd: float = 100.0,
    confidence_level: int = 90,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Estimate transaction completion time and timeout threshold.

    Uses historical data and current network conditions to predict:
    - Expected completion time
    - Recommended timeout threshold
    - Confidence intervals (P50, P75, P90, P95, P99)
    - Delay risk assessment
    - Monitoring recommendations

    Query Parameters:
    - bridge_name: Bridge protocol to use
    - source_chain: Source blockchain
    - destination_chain: Destination blockchain
    - amount_usd: Transaction amount in USD (affects estimate)
    - confidence_level: Confidence % for timeout (50, 75, 90, 95, 99)

    Perfect for:
    - Setting transaction timeouts
    - Monitoring transaction progress
    - SLA planning
    - Risk assessment
    """
    try:
        # Validate confidence level
        valid_levels = [50, 75, 90, 95, 99]
        if confidence_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"confidence_level must be one of: {valid_levels}"
            )

        log.info(
            f"Timeout estimate requested: {bridge_name} {source_chain} -> {destination_chain}, "
            f"amount: ${amount_usd}, confidence: {confidence_level}%"
        )

        # Get estimate
        estimate = timeout_estimator.estimate_timeout(
            bridge_name=bridge_name.lower(),
            source_chain=source_chain.lower(),
            destination_chain=destination_chain.lower(),
            amount_usd=amount_usd,
            db=db,
            confidence_level=confidence_level
        )

        return estimate

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error estimating timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate timeout: {str(e)}"
        )


@router.post("/batch-timeout-estimates")
async def batch_timeout_estimates(
    estimates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get timeout estimates for multiple routes in batch.

    Request body: List of estimate requests
    [
        {
            "bridge_name": "across",
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "amount_usd": 1000,
            "confidence_level": 90
        },
        ...
    ]

    Returns timeout estimates for all routes.
    """
    try:
        if len(estimates) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 estimates per batch"
            )

        results = []

        for req in estimates:
            try:
                estimate = timeout_estimator.estimate_timeout(
                    bridge_name=req.get("bridge_name", "").lower(),
                    source_chain=req.get("source_chain", "").lower(),
                    destination_chain=req.get("destination_chain", "").lower(),
                    amount_usd=req.get("amount_usd", 100.0),
                    db=db,
                    confidence_level=req.get("confidence_level", 90)
                )
                results.append(estimate)
            except Exception as e:
                log.error(f"Error in batch estimate: {str(e)}")
                results.append({
                    "error": str(e),
                    "bridge_name": req.get("bridge_name"),
                    "source_chain": req.get("source_chain"),
                    "destination_chain": req.get("destination_chain")
                })

        return {
            "total_estimates": len(results),
            "estimates": results,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error processing batch estimates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch estimates: {str(e)}"
        )
