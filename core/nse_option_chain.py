"""NSE option chain data fetcher for NIFTY 50."""

from __future__ import annotations

import time
import warnings
from typing import Any, Dict

import requests

# Suppress urllib3 OpenSSL warning on macOS (LibreSSL compatibility)
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")


class NSEDataFetchError(RuntimeError):
    """Raised when NSE option chain data cannot be fetched."""


_NSE_HOME_URL = "https://www.nseindia.com"
_NSE_OPTION_CHAIN_URL = (
    "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": _NSE_HOME_URL,
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


def fetch_nifty_option_chain(
    *,
    max_retries: int = 3,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    """Fetch raw NSE option chain JSON for NIFTY 50.

    This function handles NSE's cookie requirements by first visiting the
    homepage to establish a session, then fetching the option chain data.
    It includes retry logic with exponential backoff for reliability.

    Args:
        max_retries: Number of attempts before failing. Must be >= 1.
        timeout_seconds: Request timeout per attempt in seconds.

    Returns:
        Raw JSON dictionary from NSE API containing option chain data.

    Raises:
        NSEDataFetchError: When data cannot be fetched after all retries.
        ValueError: When max_retries is less than 1.
    """
    if max_retries < 1:
        raise ValueError("max_retries must be >= 1")

    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)

    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            # Prime session cookies by visiting NSE homepage
            # NSE requires cookies to be set before API calls
            # Visit homepage first to establish session
            home_resp = session.get(_NSE_HOME_URL, timeout=timeout_seconds)
            home_resp.raise_for_status()

            # Wait a bit to simulate human behavior
            time.sleep(2.0)  # Increased delay

            # Visit the actual option chain page first (this is critical)
            # NSE often requires visiting the web page before API access
            option_chain_page = f"{_NSE_HOME_URL}/option-chain"
            try:
                page_resp = session.get(option_chain_page, timeout=timeout_seconds)
                # Don't raise on error, just establish session
                time.sleep(1.5)
            except Exception:
                # If page fails, continue anyway
                pass

            # Visit market data page to further establish session
            market_url = f"{_NSE_HOME_URL}/market-data/equity-derivatives-watch"
            try:
                session.get(market_url, timeout=timeout_seconds)
                time.sleep(1.0)  # Increased delay
            except Exception:
                # If market page fails, continue anyway
                pass

            # Update headers for API call - critical headers for NSE API
            api_headers = {
                "User-Agent": _DEFAULT_HEADERS["User-Agent"],
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": f"{_NSE_HOME_URL}/option-chain",
                "Origin": _NSE_HOME_URL,
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "X-Requested-With": "XMLHttpRequest",
            }

            # Fetch option chain data
            response = session.get(
                _NSE_OPTION_CHAIN_URL,
                headers=api_headers,
                timeout=timeout_seconds,
            )
            
            # Check for 403 specifically
            if response.status_code == 403:
                # Provide helpful error message
                error_msg = (
                    f"403 Forbidden: NSE is blocking the request. "
                    f"This can happen when:\n"
                    f"1. Market is closed (NSE trading hours: 9:15 AM - 3:30 PM IST, Mon-Fri)\n"
                    f"2. Too many requests from your IP\n"
                    f"3. NSE's anti-scraping measures detected automated access\n\n"
                    f"Try again during market hours or wait 10-15 minutes."
                )
                raise NSEDataFetchError(error_msg)
            
            response.raise_for_status()

            # Check if response is empty
            if not response.text or len(response.text.strip()) == 0:
                raise NSEDataFetchError(
                    "Empty response from NSE API. This usually means:\n"
                    "1. Cookies were not properly set (try again)\n"
                    "2. Market is closed or data not available\n"
                    "3. NSE's anti-scraping measures blocked the request"
                )

            # Parse and return JSON
            try:
                json_data = response.json()
                
                # Check if JSON is empty or invalid
                if not json_data or (isinstance(json_data, dict) and len(json_data) == 0):
                    raise NSEDataFetchError(
                        "Received empty JSON response from NSE API. "
                        "This may indicate session/cookie issues. Try again."
                    )
                
                return json_data
            except ValueError as json_err:
                # JSON parsing errors are not retryable
                raise NSEDataFetchError(
                    f"Failed to parse JSON response: {json_err}. "
                    f"Response text (first 200 chars): {response.text[:200]}"
                ) from json_err

        except requests.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else "unknown"
            last_error = NSEDataFetchError(
                f"HTTP error {status_code}: {http_err}"
            )
        except requests.RequestException as req_err:
            last_error = NSEDataFetchError(
                f"Request failed: {req_err}"
            )
        except NSEDataFetchError as nse_err:
            # Re-raise NSEDataFetchError immediately (non-retryable errors)
            raise
        except Exception as exc:
            last_error = NSEDataFetchError(
                f"Unexpected error: {exc}"
            )

        # Retry with exponential backoff (longer delays for 403 errors)
        if attempt < max_retries:
            # Longer delay for 403 errors
            if isinstance(last_error, NSEDataFetchError) and "403" in str(last_error):
                wait_time = attempt * 3  # 3, 6, 9 seconds
            else:
                wait_time = attempt
            time.sleep(wait_time)
            continue

    # All retries exhausted
    raise NSEDataFetchError(
        f"Failed to fetch NIFTY option chain after {max_retries} attempt(s). "
        f"Last error: {last_error}"
    )
