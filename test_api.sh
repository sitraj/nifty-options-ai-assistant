#!/bin/bash
# Test script for NSE Option Chain API using curl

# Step 1: Visit homepage to get cookies (save to cookie jar)
echo "Step 1: Visiting NSE homepage to establish session..."
curl -c cookies.txt -b cookies.txt \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Connection: keep-alive" \
  -H "Upgrade-Insecure-Requests: 1" \
  -H "Sec-Fetch-Dest: document" \
  -H "Sec-Fetch-Mode: navigate" \
  -H "Sec-Fetch-Site: none" \
  -H "Cache-Control: max-age=0" \
  -L "https://www.nseindia.com" \
  -o /dev/null -s

sleep 2

# Step 2: Visit option chain page (update cookies)
echo "Step 2: Visiting option chain page..."
curl -c cookies.txt -b cookies.txt \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Referer: https://www.nseindia.com" \
  -H "Connection: keep-alive" \
  -H "Upgrade-Insecure-Requests: 1" \
  -H "Sec-Fetch-Dest: document" \
  -H "Sec-Fetch-Mode: navigate" \
  -H "Sec-Fetch-Site: same-origin" \
  -L "https://www.nseindia.com/option-chain" \
  -o /dev/null -s

sleep 1

# Step 3: Make API call with all cookies and headers
echo "Step 3: Calling NSE Option Chain API..."
curl -b cookies.txt \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Referer: https://www.nseindia.com/option-chain" \
  -H "Origin: https://www.nseindia.com" \
  -H "Connection: keep-alive" \
  -H "Sec-Fetch-Dest: empty" \
  -H "Sec-Fetch-Mode: cors" \
  -H "Sec-Fetch-Site: same-origin" \
  -H "X-Requested-With: XMLHttpRequest" \
  "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY" \
  | python3 -m json.tool

# Cleanup
rm -f cookies.txt

echo ""
echo "Done! If you see JSON data above, the API call was successful."
echo "If you see empty response or error, cookies may not be set properly."
