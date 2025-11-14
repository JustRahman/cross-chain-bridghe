# Nexbridge API - Complete Examples with Real Outputs

Generated: Tue Nov 11 18:09:36 MST 2025

This document shows all API endpoints with actual request/response examples.

---

# 1. Health Endpoints

## Health Check

**Request:**
```bash
curl -X GET "http://localhost:8000/health" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-11-12T01:09:36.637630",
    "version": "1.0.0"
}
```

---

## Detailed Health

**Request:**
```bash
curl -X GET "http://localhost:8000/health/detailed" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "status": "degraded",
    "timestamp": "2025-11-12T01:09:36.753303",
    "version": "1.0.0",
    "checks": {
        "database": "unhealthy: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')",
        "redis": "healthy"
    }
}
```

---

## Readiness Check

**Request:**
```bash
curl -X GET "http://localhost:8000/health/ready" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
[
    {
        "status": "not ready"
    },
    503
]
```

---

## Liveness Check

**Request:**
```bash
curl -X GET "http://localhost:8000/health/live" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "status": "alive"
}
```

---

# 2. Routes Endpoints

## Get Bridge Quotes

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/routes/quote" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}'
```

**Response:**
```json
{
    "routes": [
        {
            "bridge_name": "Across Protocol",
            "route_type": "direct",
            "estimated_time_seconds": 180,
            "cost_breakdown": {
                "bridge_fee_usd": 1.0,
                "gas_cost_source_usd": 5.0,
                "gas_cost_destination_usd": 0.05,
                "total_cost_usd": 6.05,
                "slippage_percentage": 0.1
            },
            "success_rate": 99.5,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "bridge",
                    "description": "Bridge to arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "1000000000000"
        },
        {
            "bridge_name": "Celer cBridge",
            "route_type": "direct",
            "estimated_time_seconds": 180,
            "cost_breakdown": {
                "bridge_fee_usd": 0.4,
                "gas_cost_source_usd": 6.0,
                "gas_cost_destination_usd": 0.15,
                "total_cost_usd": 6.55,
                "slippage_percentage": 0.2
            },
            "success_rate": 98.8,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "send",
                    "description": "Send via Celer to arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "5000000000000"
        },
        {
            "bridge_name": "Orbiter Finance",
            "route_type": "direct",
            "estimated_time_seconds": 300,
            "cost_breakdown": {
                "bridge_fee_usd": 0.3,
                "gas_cost_source_usd": 5.0,
                "gas_cost_destination_usd": 0.1,
                "total_cost_usd": 5.4,
                "slippage_percentage": 0.1
            },
            "success_rate": 99.2,
            "steps": [
                {
                    "action": "send",
                    "description": "Transfer to arbitrum via Orbiter"
                }
            ],
            "requires_approval": false,
            "minimum_amount": "5000000",
            "maximum_amount": "10000000000"
        },
        {
            "bridge_name": "Hop Protocol",
            "route_type": "direct",
            "estimated_time_seconds": 300,
            "cost_breakdown": {
                "bridge_fee_usd": 0.0,
                "gas_cost_source_usd": 6.0,
                "gas_cost_destination_usd": 0.0,
                "total_cost_usd": 6.0,
                "slippage_percentage": 0.5
            },
            "success_rate": 97.5,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "bridge",
                    "description": "Bridge to arbitrum via AMM"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "10000000000000"
        },
        {
            "bridge_name": "Connext",
            "route_type": "direct",
            "estimated_time_seconds": 300,
            "cost_breakdown": {
                "bridge_fee_usd": 1.0,
                "gas_cost_source_usd": 7.0,
                "gas_cost_destination_usd": 0.1,
                "total_cost_usd": 8.1,
                "slippage_percentage": 0.3
            },
            "success_rate": 97.5,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "bridge",
                    "description": "Bridge via router network to arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "1000000000000"
        },
        {
            "bridge_name": "Stargate Finance",
            "route_type": "direct",
            "estimated_time_seconds": 240,
            "cost_breakdown": {
                "bridge_fee_usd": 0.6,
                "gas_cost_source_usd": 8.0,
                "gas_cost_destination_usd": 0.75,
                "total_cost_usd": 9.35,
                "slippage_percentage": 0.05
            },
            "success_rate": 98.8,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "bridge",
                    "description": "Bridge via LayerZero to arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "500000000000"
        },
        {
            "bridge_name": "Synapse Protocol",
            "route_type": "direct",
            "estimated_time_seconds": 360,
            "cost_breakdown": {
                "bridge_fee_usd": 0.8,
                "gas_cost_source_usd": 7.5,
                "gas_cost_destination_usd": 0.25,
                "total_cost_usd": 8.55,
                "slippage_percentage": 0.3
            },
            "success_rate": 96.5,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "swap_bridge",
                    "description": "Swap and bridge to arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "5000000000000"
        },
        {
            "bridge_name": "LayerZero",
            "route_type": "direct",
            "estimated_time_seconds": 300,
            "cost_breakdown": {
                "bridge_fee_usd": 0.35,
                "gas_cost_source_usd": 9.0,
                "gas_cost_destination_usd": 0.3,
                "total_cost_usd": 9.65,
                "slippage_percentage": 0.1
            },
            "success_rate": 98.0,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "send_message",
                    "description": "Send LayerZero message"
                },
                {
                    "action": "relay",
                    "description": "Relay to arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "50000000000000"
        },
        {
            "bridge_name": "deBridge",
            "route_type": "direct",
            "estimated_time_seconds": 420,
            "cost_breakdown": {
                "bridge_fee_usd": 0.7,
                "gas_cost_source_usd": 8.0,
                "gas_cost_destination_usd": 0.2,
                "total_cost_usd": 8.9,
                "slippage_percentage": 0.3
            },
            "success_rate": 97.8,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "create_order",
                    "description": "Create DLN order"
                },
                {
                    "action": "fulfill",
                    "description": "Fulfill on arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "10000000000000"
        },
        {
            "bridge_name": "Wormhole",
            "route_type": "direct",
            "estimated_time_seconds": 600,
            "cost_breakdown": {
                "bridge_fee_usd": 0.25,
                "gas_cost_source_usd": 10.0,
                "gas_cost_destination_usd": 0.5,
                "total_cost_usd": 10.75,
                "slippage_percentage": 0.1
            },
            "success_rate": 95.0,
            "steps": [
                {
                    "action": "approve",
                    "description": "Approve token spending"
                },
                {
                    "action": "lock",
                    "description": "Lock tokens in Wormhole contract"
                },
                {
                    "action": "wait",
                    "description": "Wait for guardian signatures"
                },
                {
                    "action": "redeem",
                    "description": "Redeem on arbitrum"
                }
            ],
            "requires_approval": true,
            "minimum_amount": "1000000",
            "maximum_amount": "10000000000000"
        }
    ],
    "quote_id": "quote_0eca08e18b844e83",
    "expires_at": 1762910077
}
```

---

## Batch Quote Requests

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/routes/batch-quote" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"quotes":[{"source_chain":"ethereum","destination_chain":"arbitrum","source_token":"USDC","destination_token":"USDC","amount":"1000000000"}]}'
```

**Response:**
```json
{
    "results": [
        {
            "request_index": 0,
            "success": false,
            "quote": null,
            "error": "'BridgeQuote' object has no attribute 'estimated_time'"
        }
    ],
    "total_requests": 1,
    "successful": 0,
    "failed": 1,
    "processing_time_ms": 0
}
```

---

## Timeout Estimate

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/routes/timeout-estimate?bridge_name=across&source_chain=ethereum&destination_chain=arbitrum&amount_usd=1000&confidence_level=90" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "bridge_name": "across",
    "source_chain": "ethereum",
    "destination_chain": "arbitrum",
    "estimates": {
        "expected_time_minutes": 15,
        "timeout_minutes": 30,
        "confidence_level": 90
    },
    "risk_assessment": {
        "delay_risk": "unknown",
        "network_condition": "unknown",
        "amount_impact": "unknown"
    },
    "recommendations": {
        "set_timeout_at": 30,
        "check_status_after": 10,
        "escalate_after": 20,
        "consider_alternative_after": 30
    },
    "data_quality": {
        "sample_size": 0,
        "confidence": "low",
        "warning": "Insufficient historical data - using conservative estimates"
    },
    "estimated_at": "2025-11-12T01:09:37.669935"
}
```

---

## Batch Timeout Estimates

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/routes/batch-timeout-estimates" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '[{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","amount_usd":1000,"confidence_level":90}]'
```

**Response:**
```json
{
    "total_estimates": 1,
    "estimates": [
        {
            "bridge_name": "across",
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "estimates": {
                "expected_time_minutes": 15,
                "timeout_minutes": 30,
                "confidence_level": 90
            },
            "risk_assessment": {
                "delay_risk": "unknown",
                "network_condition": "unknown",
                "amount_impact": "unknown"
            },
            "recommendations": {
                "set_timeout_at": 30,
                "check_status_after": 10,
                "escalate_after": 20,
                "consider_alternative_after": 30
            },
            "data_quality": {
                "sample_size": 0,
                "confidence": "low",
                "warning": "Insufficient historical data - using conservative estimates"
            },
            "estimated_at": "2025-11-12T01:09:37.759768"
        }
    ],
    "generated_at": "2025-11-12T01:09:37.759778"
}
```

---

# 3. Bridges Endpoints

## Bridge Status

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/bridges/status" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "bridges": [
        {
            "name": "Across Protocol",
            "protocol": "across",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 99.5,
            "average_completion_time": 180,
            "uptime_percentage": 99.8,
            "last_health_check": "2025-11-12T01:09:38.310628",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base"
            ]
        },
        {
            "name": "Stargate Finance",
            "protocol": "stargate",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 98.8,
            "average_completion_time": 240,
            "uptime_percentage": 99.5,
            "last_health_check": "2025-11-12T01:09:38.311923",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "43114",
                "250"
            ]
        },
        {
            "name": "Hop Protocol",
            "protocol": "hop",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 96.0,
            "average_completion_time": 420,
            "uptime_percentage": 98.0,
            "last_health_check": "2025-11-12T01:09:38.312883",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "100"
            ]
        },
        {
            "name": "Connext",
            "protocol": "connext",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 97.5,
            "average_completion_time": 300,
            "uptime_percentage": 99.2,
            "last_health_check": "2025-11-12T01:09:38.313823",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "56",
                "100"
            ]
        },
        {
            "name": "Wormhole",
            "protocol": "wormhole",
            "is_healthy": false,
            "is_active": true,
            "success_rate": 85.0,
            "average_completion_time": 300,
            "uptime_percentage": 90.0,
            "last_health_check": "2025-11-12T01:09:38.314740",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "56",
                "43114",
                "250",
                "1284"
            ]
        },
        {
            "name": "Synapse Protocol",
            "protocol": "synapse",
            "is_healthy": false,
            "is_active": true,
            "success_rate": 85.0,
            "average_completion_time": 300,
            "uptime_percentage": 90.0,
            "last_health_check": "2025-11-12T01:09:38.315506",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "56",
                "43114",
                "250",
                "1666600000"
            ]
        },
        {
            "name": "Celer cBridge",
            "protocol": "celer",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 95.0,
            "average_completion_time": 300,
            "uptime_percentage": 98.0,
            "last_health_check": "2025-11-12T01:09:38.316152",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "56",
                "43114",
                "250",
                "42220"
            ]
        },
        {
            "name": "Orbiter Finance",
            "protocol": "orbiter",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 95.0,
            "average_completion_time": 300,
            "uptime_percentage": 98.0,
            "last_health_check": "2025-11-12T01:09:38.316773",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "base",
                "324",
                "59144"
            ]
        },
        {
            "name": "deBridge",
            "protocol": "debridge",
            "is_healthy": true,
            "is_active": true,
            "success_rate": 95.0,
            "average_completion_time": 300,
            "uptime_percentage": 98.0,
            "last_health_check": "2025-11-12T01:09:38.317479",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "56",
                "43114",
                "250",
                "42220",
                "100"
            ]
        },
        {
            "name": "LayerZero",
            "protocol": "layerzero",
            "is_healthy": false,
            "is_active": true,
            "success_rate": 85.0,
            "average_completion_time": 300,
            "uptime_percentage": 90.0,
            "last_health_check": "2025-11-12T01:09:38.317959",
            "supported_chains": [
                "ethereum",
                "optimism",
                "arbitrum",
                "polygon",
                "base",
                "56",
                "43114",
                "250",
                "42220",
                "100",
                "324"
            ]
        }
    ],
    "total_bridges": 10,
    "healthy_bridges": 7,
    "checked_at": "2025-11-12T01:09:38.318168"
}
```

---

## Supported Tokens

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/bridges/tokens/supported" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "tokens": [
        {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "decimals": 6,
            "chain": "ethereum"
        },
        {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "decimals": 6,
            "chain": "arbitrum"
        },
        {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "decimals": 6,
            "chain": "ethereum"
        },
        {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "decimals": 18,
            "chain": "ethereum"
        },
        {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "decimals": 18,
            "chain": "ethereum"
        }
    ],
    "total_tokens": 5
}
```

---

# 4. Transactions Endpoints

## Track Transaction

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/track/0x123456789abcdef" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "transaction": {
        "transaction_hash": "0x123456789abcdef",
        "bridge_protocol": "across",
        "source_chain": "ethereum",
        "destination_chain": "arbitrum",
        "status": "completed",
        "amount": "100000000",
        "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "created_at": "2025-11-12T01:04:38.520247",
        "completed_at": "2025-11-12T01:07:38.520260",
        "estimated_completion": null,
        "steps_completed": 4,
        "total_steps": 4,
        "error_message": null
    },
    "progress_percentage": 100.0,
    "current_step": "Transaction completed successfully"
}
```

---

## Bridge Statistics

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/statistics/bridges" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "statistics": [
        {
            "bridge_name": "LayerZero",
            "protocol": "layerzero",
            "total_transactions": 2350,
            "successful_transactions": 2230,
            "failed_transactions": 120,
            "success_rate": "101.5",
            "average_completion_time": 780,
            "total_volume_usd": "14000000",
            "uptime_percentage": "101.1999999999999997",
            "cheapest_route_count": 230,
            "fastest_route_count": 180
        },
        {
            "bridge_name": "deBridge",
            "protocol": "debridge",
            "total_transactions": 2200,
            "successful_transactions": 2090,
            "failed_transactions": 110,
            "success_rate": "101.0",
            "average_completion_time": 720,
            "total_volume_usd": "13000000",
            "uptime_percentage": "100.9",
            "cheapest_route_count": 210,
            "fastest_route_count": 165
        },
        {
            "bridge_name": "Orbiter Finance",
            "protocol": "orbiter",
            "total_transactions": 2050,
            "successful_transactions": 1950,
            "failed_transactions": 100,
            "success_rate": "100.5",
            "average_completion_time": 660,
            "total_volume_usd": "12000000",
            "uptime_percentage": "100.6",
            "cheapest_route_count": 190,
            "fastest_route_count": 150
        },
        {
            "bridge_name": "Celer cBridge",
            "protocol": "celer",
            "total_transactions": 1900,
            "successful_transactions": 1810,
            "failed_transactions": 90,
            "success_rate": "100.0",
            "average_completion_time": 600,
            "total_volume_usd": "11000000",
            "uptime_percentage": "100.2999999999999998",
            "cheapest_route_count": 170,
            "fastest_route_count": 135
        },
        {
            "bridge_name": "Synapse Protocol",
            "protocol": "synapse",
            "total_transactions": 1750,
            "successful_transactions": 1670,
            "failed_transactions": 80,
            "success_rate": "99.5",
            "average_completion_time": 540,
            "total_volume_usd": "10000000",
            "uptime_percentage": "100.0",
            "cheapest_route_count": 150,
            "fastest_route_count": 120
        },
        {
            "bridge_name": "Wormhole",
            "protocol": "wormhole",
            "total_transactions": 1600,
            "successful_transactions": 1530,
            "failed_transactions": 70,
            "success_rate": "99.0",
            "average_completion_time": 480,
            "total_volume_usd": "9000000",
            "uptime_percentage": "99.7",
            "cheapest_route_count": 130,
            "fastest_route_count": 105
        },
        {
            "bridge_name": "Connext",
            "protocol": "connext",
            "total_transactions": 1450,
            "successful_transactions": 1390,
            "failed_transactions": 60,
            "success_rate": "98.5",
            "average_completion_time": 420,
            "total_volume_usd": "8000000",
            "uptime_percentage": "99.3999999999999999",
            "cheapest_route_count": 110,
            "fastest_route_count": 90
        },
        {
            "bridge_name": "Hop Protocol",
            "protocol": "hop",
            "total_transactions": 1300,
            "successful_transactions": 1250,
            "failed_transactions": 50,
            "success_rate": "98.0",
            "average_completion_time": 360,
            "total_volume_usd": "7000000",
            "uptime_percentage": "99.1",
            "cheapest_route_count": 90,
            "fastest_route_count": 75
        },
        {
            "bridge_name": "Stargate Finance",
            "protocol": "stargate",
            "total_transactions": 1150,
            "successful_transactions": 1110,
            "failed_transactions": 40,
            "success_rate": "97.5",
            "average_completion_time": 300,
            "total_volume_usd": "6000000",
            "uptime_percentage": "98.8",
            "cheapest_route_count": 70,
            "fastest_route_count": 60
        },
        {
            "bridge_name": "Across Protocol",
            "protocol": "across",
            "total_transactions": 1000,
            "successful_transactions": 970,
            "failed_transactions": 30,
            "success_rate": "97.0",
            "average_completion_time": 240,
            "total_volume_usd": "5000000",
            "uptime_percentage": "98.5",
            "cheapest_route_count": 50,
            "fastest_route_count": 45
        }
    ],
    "total_transactions": 16750,
    "total_volume_usd": "95000000",
    "period_start": "2025-11-05T01:09:38.604461",
    "period_end": "2025-11-12T01:09:38.604473"
}
```

---

## Chain Statistics

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/statistics/chains" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "chains": [
        {
            "chain_name": "ethereum",
            "chain_id": 1,
            "outbound_transactions": 850,
            "inbound_transactions": 920,
            "total_volume_usd": "12500000",
            "most_popular_destination": "arbitrum",
            "average_transaction_size_usd": "15000"
        },
        {
            "chain_name": "arbitrum",
            "chain_id": 42161,
            "outbound_transactions": 720,
            "inbound_transactions": 850,
            "total_volume_usd": "8900000",
            "most_popular_destination": "ethereum",
            "average_transaction_size_usd": "12000"
        },
        {
            "chain_name": "optimism",
            "chain_id": 10,
            "outbound_transactions": 580,
            "inbound_transactions": 640,
            "total_volume_usd": "6200000",
            "most_popular_destination": "ethereum",
            "average_transaction_size_usd": "10500"
        },
        {
            "chain_name": "polygon",
            "chain_id": 137,
            "outbound_transactions": 950,
            "inbound_transactions": 780,
            "total_volume_usd": "5800000",
            "most_popular_destination": "ethereum",
            "average_transaction_size_usd": "6100"
        },
        {
            "chain_name": "base",
            "chain_id": 8453,
            "outbound_transactions": 420,
            "inbound_transactions": 510,
            "total_volume_usd": "4100000",
            "most_popular_destination": "ethereum",
            "average_transaction_size_usd": "9800"
        }
    ],
    "generated_at": "2025-11-12T01:09:38.687936"
}
```

---

# 5. Utilities Endpoints

## Gas Prices (Ethereum)

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/utilities/gas-prices/1" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "chain_id": 1,
    "chain_name": "ethereum",
    "slow": 20.0,
    "standard": 30.0,
    "fast": 40.0,
    "rapid": 50.0,
    "estimated_cost_usd": {
        "slow": {
            "simple_transfer": 0.84,
            "bridge_transaction": 8.0
        },
        "standard": {
            "simple_transfer": 1.26,
            "bridge_transaction": 12.0
        },
        "fast": {
            "simple_transfer": 1.68,
            "bridge_transaction": 16.0
        },
        "rapid": {
            "simple_transfer": 2.1,
            "bridge_transaction": 20.0
        }
    }
}
```

---

## All Gas Prices

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/utilities/gas-prices" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "chains": {
        "ethereum": {
            "chain_id": 1,
            "slow": 20,
            "standard": 30,
            "fast": 40,
            "rapid": 50
        },
        "optimism": {
            "chain_id": 10,
            "slow": 0.001,
            "standard": 0.002,
            "fast": 0.003,
            "rapid": 0.005
        },
        "arbitrum": {
            "chain_id": 42161,
            "slow": 0.1,
            "standard": 0.15,
            "fast": 0.2,
            "rapid": 0.3
        },
        "polygon": {
            "chain_id": 137,
            "slow": 56.239272087,
            "standard": 57.751276647,
            "fast": 60.54244652,
            "rapid": 78.705180476
        },
        "base": {
            "chain_id": 8453,
            "slow": 0.001,
            "standard": 0.002,
            "fast": 0.003,
            "rapid": 0.005
        },
        "bnb": {
            "chain_id": 56,
            "slow": 3,
            "standard": 5,
            "fast": 7,
            "rapid": 10
        },
        "avalanche": {
            "chain_id": 43114,
            "slow": 25,
            "standard": 30,
            "fast": 40,
            "rapid": 50
        }
    },
    "total_chains": 7
}
```

---

## Token Price (USDC)

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/utilities/token-price/USDC" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "detail": "Token USDC not found or not supported"
}
```

---

## All Token Prices

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/utilities/token-prices" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "tokens": {
        "USDC": 0.999785,
        "USDT": 0.999548,
        "DAI": 0.998547,
        "WETH": 3419.16,
        "ETH": 3424.54,
        "BNB": 958.83,
        "AVAX": 16.98,
        "FTM": 0.142913,
        "OP": 0.406129,
        "ARB": 0.275188
    },
    "total_tokens": 10,
    "last_updated": "2025-11-12T01:09:39.834827"
}
```

---

## Calculate Savings

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/utilities/calculate-savings" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"amount_usd":"1000.00","cheapest_route_cost":"10.50","expensive_route_cost":"25.75"}'
```

**Response:**
```json
{
    "amount_usd": "1000.00",
    "cheapest_route_cost": "10.50",
    "expensive_route_cost": "25.75",
    "savings_usd": "15.25",
    "savings_percentage": "59.22",
    "recommendation": "Excellent savings! Using the cheapest route saves you over 50% in fees."
}
```

---

# 6. Transaction History Endpoints

## List Transactions

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/transaction-history/?page=1&limit=10" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "transactions": [],
    "total": 0,
    "page": 1,
    "page_size": 20
}
```

---

## Simulate Transaction

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/transaction-history/simulate" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","bridge":"across"}'
```

**Response:**
```json
{
    "success_probability": 0.9309999999999999,
    "estimated_slippage": 0.1,
    "warnings": [],
    "simulation_result": {
        "estimated_slippage_percent": 0.1,
        "min_received_amount": "999000000",
        "max_slippage_tolerated": 2.0,
        "liquidity_check": "sufficient",
        "gas_estimate_gwei": 25.0,
        "total_time_estimate_minutes": 5
    },
    "risk_level": "low",
    "recommended_action": "Safe to proceed"
}
```

---

# 7. Webhooks Endpoints

## List Webhooks

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/webhooks/" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "webhooks": [
        {
            "id": 6,
            "url": "https://example.com/webhook",
            "is_active": true,
            "events": [
                "transaction.completed"
            ],
            "chain_filter": null,
            "bridge_filter": null,
            "user_email": null,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_triggered_at": null,
            "created_at": "2025-11-12T00:49:26.694561Z",
            "updated_at": null
        },
        {
            "id": 5,
            "url": "https://example.com/webhook",
            "is_active": true,
            "events": [
                "transaction.completed"
            ],
            "chain_filter": null,
            "bridge_filter": null,
            "user_email": null,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_triggered_at": null,
            "created_at": "2025-11-12T00:46:57.044660Z",
            "updated_at": null
        },
        {
            "id": 4,
            "url": "https://example.com/webhook",
            "is_active": true,
            "events": [
                "transaction.completed"
            ],
            "chain_filter": null,
            "bridge_filter": null,
            "user_email": null,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_triggered_at": null,
            "created_at": "2025-11-12T00:41:59.371014Z",
            "updated_at": null
        },
        {
            "id": 3,
            "url": "https://example.com/webhook",
            "is_active": true,
            "events": [
                "transaction.completed"
            ],
            "chain_filter": null,
            "bridge_filter": null,
            "user_email": null,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_triggered_at": null,
            "created_at": "2025-11-12T00:39:18.796248Z",
            "updated_at": null
        },
        {
            "id": 2,
            "url": "https://example.com/webhook",
            "is_active": true,
            "events": [
                "transaction.completed"
            ],
            "chain_filter": null,
            "bridge_filter": null,
            "user_email": null,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_triggered_at": null,
            "created_at": "2025-11-12T00:36:22.657298Z",
            "updated_at": null
        },
        {
            "id": 1,
            "url": "https://example.com/webhook",
            "is_active": true,
            "events": [
                "transaction.completed"
            ],
            "chain_filter": null,
            "bridge_filter": null,
            "user_email": null,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_triggered_at": null,
            "created_at": "2025-11-12T00:35:31.401550Z",
            "updated_at": null
        }
    ],
    "total": 6
}
```

---

# 8. Slippage Endpoints

## Calculate Slippage

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/slippage/calculate" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"bridge_name":"across","source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","available_liquidity":"50000000000"}'
```

**Response:**
```json
{
    "estimated_slippage_percent": 0.2,
    "min_received_amount": "998000000",
    "max_slippage_percent": 2.0,
    "risk_level": "low",
    "warnings": [
        "Transaction parameters are within safe ranges"
    ],
    "recommendation": "SAFE TO PROCEED - Slippage of 0.20% is within acceptable ranges.",
    "liquidity_utilization": 2.0,
    "breakdown": {
        "base_slippage": 0.05,
        "liquidity_impact": 0.1,
        "bridge_factor": 0.05
    }
}
```

---

## Protection Parameters

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/slippage/protection-parameters" \
  -H "X-API-Key: nxb_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"source_chain":"ethereum","destination_chain":"arbitrum","token":"USDC","amount":"1000000000","risk_tolerance":"medium"}'
```

**Response:**
```json
{
    "min_amount_out": "980000000",
    "max_slippage_bps": 200,
    "deadline": 1762910680,
    "amount_in": "1000000000",
    "protection_enabled": true
}
```

---

## Historical Slippage

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/slippage/historical/across/ethereum/arbitrum?days=7" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "average_slippage": 0.5,
    "max_slippage": 1.0,
    "min_slippage": 0.1,
    "sample_size": 0,
    "period_hours": 24
}
```

---

# 9. Gas Optimization Endpoints

## Optimal Timing

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/gas-optimization/optimal-timing/1" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "current_gas_price_gwei": 30.0,
    "average_24h_gwei": 30.0,
    "min_24h_gwei": 20.0,
    "max_24h_gwei": 50.0,
    "optimal_hour_utc": 2,
    "optimal_price_gwei": 25.0,
    "potential_savings_percent": 0.0,
    "potential_savings_usd": 0.0,
    "recommendation": "execute_now",
    "message": "Insufficient historical data for analysis. Current prices appear reasonable.",
    "price_trend": "unknown",
    "hourly_averages": {},
    "forecast_next_hours": [],
    "analysis_timestamp": "2025-11-12T01:09:40.485062"
}
```

---

## Compare Timing

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/gas-optimization/compare-timing/1?amount_usd=1000" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "execute_now": {
        "gas_cost_usd": 12.0,
        "total_cost_usd": 1012.0,
        "wait_time_hours": 0,
        "recommendation": "Fast execution, higher cost"
    },
    "wait_for_optimal": {
        "gas_cost_usd": 10.0,
        "total_cost_usd": 1010.0,
        "wait_time_hours": 1,
        "recommendation": "Wait ~1h for 0.0% savings"
    },
    "savings": {
        "amount_usd": 2.0,
        "percent": 0.0
    },
    "best_choice": "execute_now"
}
```

---

# 10. API Keys Endpoints

## List API Keys

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/?is_active=true" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "keys": [
        {
            "id": 2,
            "name": "Development Key",
            "description": null,
            "user_email": "dev@example.com",
            "is_active": true,
            "is_revoked": false,
            "rate_limit_per_minute": 1000,
            "rate_limit_per_hour": 60000,
            "rate_limit_per_day": 1440000,
            "total_requests": 337,
            "successful_requests": 337,
            "failed_requests": 0,
            "last_used_at": "2025-11-12T01:09:40.634948",
            "allowed_endpoints": null,
            "allowed_chains": null,
            "allowed_ip_addresses": null,
            "created_at": "2025-11-11T05:12:11.169240",
            "updated_at": "2025-11-11T05:12:11.169240",
            "expires_at": null,
            "revoked_at": null,
            "revoke_reason": null
        },
        {
            "id": 1,
            "name": "Test API Key",
            "description": null,
            "user_email": "test@example.com",
            "is_active": true,
            "is_revoked": false,
            "rate_limit_per_minute": 60,
            "rate_limit_per_hour": 3600,
            "rate_limit_per_day": 86400,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "last_used_at": null,
            "allowed_endpoints": null,
            "allowed_chains": null,
            "allowed_ip_addresses": null,
            "created_at": "2025-11-11T00:39:41.332620",
            "updated_at": "2025-11-11T00:39:41.332623",
            "expires_at": null,
            "revoked_at": null,
            "revoke_reason": null
        }
    ],
    "total": 2
}
```

---

## Get API Key Usage

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/1/usage" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "stats": {
        "api_key_id": 1,
        "api_key_name": "Test API Key",
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "success_rate": 0.0,
        "requests_last_24h": 0,
        "requests_last_hour": 0,
        "most_used_endpoint": null,
        "most_used_chain": null,
        "average_response_time_ms": null,
        "last_used_at": null
    },
    "rate_limits": {
        "minute": {
            "limit": 60,
            "used": 0,
            "remaining": 60
        },
        "hour": {
            "limit": 3600,
            "used": 0,
            "remaining": 3600
        },
        "day": {
            "limit": 86400,
            "used": 0,
            "remaining": 86400
        }
    },
    "recent_errors": []
}
```

---

## Get Rate Limits

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/1/rate-limits" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "api_key_id": 1,
    "api_key_name": "Test API Key",
    "rate_limits": {
        "minute": {
            "limit": 60,
            "used": 0,
            "remaining": 60,
            "reset_in_seconds": 60
        },
        "hour": {
            "limit": 3600,
            "used": 0,
            "remaining": 3600,
            "reset_in_seconds": 3600
        },
        "day": {
            "limit": 86400,
            "used": 0,
            "remaining": 86400,
            "reset_in_seconds": 86400
        }
    }
}
```

---

## Get Violations

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/1/violations?limit=10" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "api_key_id": 1,
    "api_key_name": "Test API Key",
    "total_violations": 0,
    "violations": []
}
```

---

# 11. Analytics Endpoints

## Analytics Dashboard

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard?hours=24" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "system_health": {
        "total_requests_24h": 341,
        "total_transactions_24h": 0,
        "average_response_time_ms": 93,
        "error_rate_percent": 17.01,
        "active_api_keys": 2,
        "rate_limit_violations_24h": 0,
        "webhook_deliveries_24h": 0,
        "webhook_success_rate": 100.0
    },
    "top_endpoints": [
        {
            "endpoint": "/api/v1/transaction-history/",
            "total_requests": 15,
            "successful_requests": 8,
            "failed_requests": 7,
            "success_rate": 53.33,
            "average_response_time_ms": 8,
            "min_response_time_ms": 4,
            "max_response_time_ms": 14
        },
        {
            "endpoint": "/api/v1/routes/quote",
            "total_requests": 14,
            "successful_requests": 12,
            "failed_requests": 2,
            "success_rate": 85.71,
            "average_response_time_ms": 608,
            "min_response_time_ms": 3,
            "max_response_time_ms": 3035
        },
        {
            "endpoint": "/api/v1/webhooks/",
            "total_requests": 14,
            "successful_requests": 14,
            "failed_requests": 0,
            "success_rate": 100.0,
            "average_response_time_ms": 9,
            "min_response_time_ms": 3,
            "max_response_time_ms": 39
        },
        {
            "endpoint": "/api/v1/routes/batch-timeout-estimates",
            "total_requests": 13,
            "successful_requests": 6,
            "failed_requests": 7,
            "success_rate": 46.15,
            "average_response_time_ms": 7,
            "min_response_time_ms": 3,
            "max_response_time_ms": 20
        },
        {
            "endpoint": "/api/v1/bridges/status",
            "total_requests": 12,
            "successful_requests": 12,
            "failed_requests": 0,
            "success_rate": 100.0,
            "average_response_time_ms": 622,
            "min_response_time_ms": 480,
            "max_response_time_ms": 1187
        },
        {
            "endpoint": "/api/v1/routes/timeout-estimate",
            "total_requests": 12,
            "successful_requests": 12,
            "failed_requests": 0,
            "success_rate": 100.0,
            "average_response_time_ms": 15,
            "min_response_time_ms": 3,
            "max_response_time_ms": 58
        },
        {
            "endpoint": "/api/v1/routes/batch-quote",
            "total_requests": 12,
            "successful_requests": 11,
            "failed_requests": 1,
            "success_rate": 91.67,
            "average_response_time_ms": 378,
            "min_response_time_ms": 5,
            "max_response_time_ms": 3009
        },
        {
            "endpoint": "/api/v1/api-keys/1/violations",
            "total_requests": 11,
            "successful_requests": 6,
            "failed_requests": 5,
            "success_rate": 54.55,
            "average_response_time_ms": 9,
            "min_response_time_ms": 3,
            "max_response_time_ms": 25
        },
        {
            "endpoint": "/api/v1/routes/multi-hop",
            "total_requests": 11,
            "successful_requests": 0,
            "failed_requests": 11,
            "success_rate": 0.0,
            "average_response_time_ms": 14,
            "min_response_time_ms": 5,
            "max_response_time_ms": 38
        },
        {
            "endpoint": "/api/v1/api-keys/",
            "total_requests": 10,
            "successful_requests": 7,
            "failed_requests": 3,
            "success_rate": 70.0,
            "average_response_time_ms": 9,
            "min_response_time_ms": 2,
            "max_response_time_ms": 28
        }
    ],
    "chain_statistics": [],
    "bridge_popularity": [],
    "requests_over_time": [
        {
            "timestamp": "2025-11-11T01:09:40.984084",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T02:09:40.985087",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T03:09:40.985597",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T04:09:40.986061",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T05:09:40.986713",
            "value": 9.0
        },
        {
            "timestamp": "2025-11-11T06:09:40.987227",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T07:09:40.987681",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T08:09:40.988112",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T09:09:40.988562",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T10:09:40.989358",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T11:09:40.989872",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T12:09:40.990675",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T13:09:40.991106",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T14:09:40.991930",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T15:09:40.993108",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T16:09:40.994093",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T17:09:40.994918",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T18:09:40.995726",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T19:09:40.996506",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T20:09:40.997458",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T21:09:40.997883",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T22:09:40.998626",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T23:09:40.999160",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-12T00:09:40.999995",
            "value": 332.0
        }
    ],
    "error_rate_over_time": [
        {
            "timestamp": "2025-11-11T01:09:40.984084",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T02:09:40.985087",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T03:09:40.985597",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T04:09:40.986061",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T05:09:40.986713",
            "value": 33.33
        },
        {
            "timestamp": "2025-11-11T06:09:40.987227",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T07:09:40.987681",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T08:09:40.988112",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T09:09:40.988562",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T10:09:40.989358",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T11:09:40.989872",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T12:09:40.990675",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T13:09:40.991106",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T14:09:40.991930",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T15:09:40.993108",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T16:09:40.994093",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T17:09:40.994918",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T18:09:40.995726",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T19:09:40.996506",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T20:09:40.997458",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T21:09:40.997883",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T22:09:40.998626",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-11T23:09:40.999160",
            "value": 0.0
        },
        {
            "timestamp": "2025-11-12T00:09:40.999995",
            "value": 16.57
        }
    ],
    "generated_at": "2025-11-12T01:09:41.000877"
}
```

---

## Reliability Scores

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/reliability-scores?hours=168" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "scores": [],
    "analysis_period_hours": 168,
    "last_updated": "2025-11-12T01:09:41.082559"
}
```

---

## Bridge Reliability

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/bridge-reliability/across?hours=168" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "bridge_name": "across",
    "overall_score": 0,
    "rating": "N/A",
    "recommendation": "Insufficient data - No recent transactions found",
    "trend": "insufficient_data",
    "component_scores": {},
    "metrics": {
        "total_transactions": 0
    },
    "last_updated": "2025-11-12T01:09:41.163998"
}
```

---

## Bridge Comparison

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/bridge-comparison?bridges=across,hop,stargate&hours=168" \
  -H "X-API-Key: nxb_dev_key_12345"
```

**Response:**
```json
{
    "bridges_compared": 3,
    "analysis_period_hours": 168,
    "comparisons": [
        {
            "bridge_name": "across",
            "overall_score": 0,
            "rating": "N/A",
            "recommendation": "Insufficient data - No recent transactions found",
            "trend": "insufficient_data",
            "component_scores": {},
            "metrics": {
                "total_transactions": 0
            },
            "last_updated": "2025-11-12T01:09:41.248895"
        },
        {
            "bridge_name": "hop",
            "overall_score": 0,
            "rating": "N/A",
            "recommendation": "Insufficient data - No recent transactions found",
            "trend": "insufficient_data",
            "component_scores": {},
            "metrics": {
                "total_transactions": 0
            },
            "last_updated": "2025-11-12T01:09:41.249603"
        },
        {
            "bridge_name": "stargate",
            "overall_score": 0,
            "rating": "N/A",
            "recommendation": "Insufficient data - No recent transactions found",
            "trend": "insufficient_data",
            "component_scores": {},
            "metrics": {
                "total_transactions": 0
            },
            "last_updated": "2025-11-12T01:09:41.250253"
        }
    ],
    "best_choice": {
        "bridge_name": "across",
        "overall_score": 0,
        "rating": "N/A",
        "reason": "Highest overall reliability score"
    },
    "generated_at": "2025-11-12T01:09:41.250260"
}
```

---


---

## Summary

This file contains real request/response examples for all 35 API endpoints.

**API Key Used:** `nxb_dev_key_12345`

**Base URL:** `http://localhost:8000`

Generated on: Tue Nov 11 18:09:41 MST 2025
