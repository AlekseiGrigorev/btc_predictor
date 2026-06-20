SELECT
date, 
strftime('%Y-%m-%d %H:%M:%S', date, 'unixepoch') as date_str,
close,
source,
created_at,
strftime('%Y-%m-%d %H:%M:%S', created_at, 'unixepoch') AS created_at_str
 FROM quotes_1h
 WHERE TRUE
-- AND source = 'bybit'
ORDER BY date DESC
;