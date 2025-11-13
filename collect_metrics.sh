#!/bin/bash

# Data Collection Script
# Collects metrics from all architectures

echo "==================================="
echo "📊 COMPARATIVE METRICS COLLECTION"
echo "==================================="
echo ""

# Fetch comparative metrics from API
echo "1. API Metrics (Real-time from database):"
echo "-----------------------------------"
curl -s http://localhost:8080/api/compare/metrics | python3 -m json.tool

echo ""
echo ""
echo "2. Database Raw Data (BPC4MSA):"
echo "-----------------------------------"
docker exec bpc4msa-postgres-bpc4msa-1 psql -U bpc4msa -d audit_db -c "
  SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT event_data->>'transaction_id') as unique_transactions,
    COUNT(*) FILTER (WHERE event_type LIKE '%Violation%') as violations,
    MIN(created_at) as first_event,
    MAX(created_at) as last_event
  FROM audit_log
  WHERE created_at >= NOW() - INTERVAL '1 hour';
" 2>/dev/null

echo ""
echo "3. Database Raw Data (Synchronous):"
echo "-----------------------------------"
docker exec bpc4msa-postgres-sync-1 psql -U synchronous -d sync_db -c "
  SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT event_data->>'transaction_id') as unique_transactions,
    COUNT(*) FILTER (WHERE event_type LIKE '%Violation%') as violations,
    MIN(created_at) as first_event,
    MAX(created_at) as last_event
  FROM audit_log
  WHERE created_at >= NOW() - INTERVAL '1 hour';
" 2>/dev/null

echo ""
echo "4. Database Raw Data (Monolithic):"
echo "-----------------------------------"
docker exec bpc4msa-postgres-mono-1 psql -U monolithic -d mono_db -c "
  SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT event_data->>'transaction_id') as unique_transactions,
    COUNT(*) FILTER (WHERE event_type LIKE '%Violation%') as violations,
    MIN(created_at) as first_event,
    MAX(created_at) as last_event
  FROM audit_log
  WHERE created_at >= NOW() - INTERVAL '1 hour';
" 2>/dev/null

echo ""
echo "5. Export to CSV (Last 100 events from each architecture):"
echo "-----------------------------------"

# Export BPC4MSA events
docker exec bpc4msa-postgres-bpc4msa-1 psql -U bpc4msa -d audit_db -c "
  COPY (
    SELECT 
      id,
      event_type,
      event_data->>'transaction_id' as transaction_id,
      created_at,
      'bpc4msa' as architecture
    FROM audit_log 
    ORDER BY created_at DESC 
    LIMIT 100
  ) TO STDOUT WITH CSV HEADER;
" 2>/dev/null > /tmp/bpc4msa_events.csv

# Export Sync events
docker exec bpc4msa-postgres-sync-1 psql -U synchronous -d sync_db -c "
  COPY (
    SELECT 
      id,
      event_type,
      event_data->>'transaction_id' as transaction_id,
      created_at,
      'synchronous' as architecture
    FROM audit_log 
    ORDER BY created_at DESC 
    LIMIT 100
  ) TO STDOUT WITH CSV HEADER;
" 2>/dev/null > /tmp/sync_events.csv

# Export Mono events
docker exec bpc4msa-postgres-mono-1 psql -U monolithic -d mono_db -c "
  COPY (
    SELECT 
      id,
      event_type,
      event_data->>'transaction_id' as transaction_id,
      created_at,
      'monolithic' as architecture
    FROM audit_log 
    ORDER BY created_at DESC 
    LIMIT 100
  ) TO STDOUT WITH CSV HEADER;
" 2>/dev/null > /tmp/mono_events.csv

echo "✅ CSV files created:"
echo "   - /tmp/bpc4msa_events.csv"
echo "   - /tmp/sync_events.csv"
echo "   - /tmp/mono_events.csv"

echo ""
echo "==================================="
echo "✅ Data collection complete!"
echo "==================================="
