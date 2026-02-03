"""
Compatibility layer for older imports.

Older code used:
    from .telegram import send_price_notification

New code uses:
    from .telegram_engine import send_tanken_message / send_range_days_message
"""

from __future__ import annotations

from .telegram_engine import send_tanken_message, send_range_days_message


async def send_price_notification(*args, **kwargs):
    """Backward compatible wrapper mapping to send_tanken_message."""
    await send_tanken_message(*args, **kwargs)
