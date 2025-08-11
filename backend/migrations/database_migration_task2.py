# backend/migrations/add_cost_fields.py
"""
Database Migration for Task 2: Add Cost Calculation Fields
Run this script to add the new cost-related fields to your candidates table.
"""

import asyncio
import logging
from sqlalchemy import text
from backend.db.database import engine

# Migration SQL - Add new columns to candidates table
ADD_COST_FIELDS_SQL = """
-- Add cost-related fields to candidates table
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS rate FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS margin FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS infrastructure_cost FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS processing_cost FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS final_client_rate FLOAT DEFAULT 0.0;

-- Add tracker fields from Task 1 (if not already added)
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS notice_period VARCHAR(100),
ADD COLUMN IF NOT EXISTS availability_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS available_from TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS comments TEXT,
ADD COLUMN IF NOT EXISTS priority_level VARCHAR(20) DEFAULT 'Medium',
ADD COLUMN IF NOT EXISTS shortlist_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add comments to document the new fields
COMMENT ON COLUMN candidates.rate IS 'Candidate base hourly/daily rate';
COMMENT ON COLUMN candidates.margin IS 'Company margin amount (not percentage)';
COMMENT ON COLUMN candidates.infrastructure_cost IS 'Infrastructure costs (servers, software, etc.)';
COMMENT ON COLUMN candidates.processing_cost IS 'Processing and administrative costs';
COMMENT ON COLUMN candidates.final_client_rate IS 'Final rate charged to client (auto-calculated)';

-- Create index on final_client_rate for faster queries
CREATE INDEX IF NOT EXISTS idx_candidates_final_rate ON candidates(final_client_rate);
CREATE INDEX IF NOT EXISTS idx_candidates_status_rate ON candidates(status, final_client_rate);
"""

# Function to calculate final rates for existing records
UPDATE_EXISTING_RATES_SQL = """
-- Update final_client_rate for all existing records
UPDATE candidates 
SET final_client_rate = COALESCE(rate, 0) + COALESCE(margin, 0) + 
                       COALESCE(infrastructure_cost, 0) + COALESCE(processing_cost, 0),
    last_updated = NOW()
WHERE final_client_rate IS NULL OR final_client_rate = 0;
"""

# Verification queries
VERIFY_MIGRATION_SQL = """
-- Verify the migration was successful
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'candidates' 
    AND column_name IN ('rate', 'margin', 'infrastructure_cost', 'processing_cost', 'final_client_rate')
ORDER BY column_name;
"""

COUNT_RECORDS_SQL = """
-- Count records with cost data
SELECT 
    COUNT(*) as total_candidates,
    COUNT(rate) as candidates_with_rate,
    COUNT(final_client_rate) as candidates_with_final_rate,
    AVG(final_client_rate) as avg_final_rate
FROM candidates;
"""

async def run_migration():
    """Run the database migration to add cost fields."""
    print("🚀 Starting Task 2 Database Migration")
    print("=" * 50)
    
    try:
        async with engine.begin() as connection:
            print("📋 Adding cost-related fields to candidates table...")
            
            # Execute the migration
            await connection.execute(text(ADD_COST_FIELDS_SQL))
            print("✅ Cost fields added successfully")
            
            # Update existing records
            print("🔄 Updating final rates for existing records...")
            result = await connection.execute(text(UPDATE_EXISTING_RATES_SQL))
            print(f"✅ Updated {result.rowcount} existing records")
            
            # Verify migration
            print("🔍 Verifying migration...")
            verify_result = await connection.execute(text(VERIFY_MIGRATION_SQL))
            columns = verify_result.fetchall()
            
            print("📊 New columns added:")
            for column in columns:
                print(f"   - {column.column_name}: {column.data_type} "
                      f"(nullable: {column.is_nullable}, default: {column.column_default})")
            
            # Get record counts
            count_result = await connection.execute(text(COUNT_RECORDS_SQL))
            stats = count_result.fetchone()
            
            print(f"\n📈 Database Statistics:")
            print(f"   - Total candidates: {stats.total_candidates}")
            print(f"   - Candidates with rate: {stats.candidates_with_rate}")
            print(f"   - Candidates with final rate: {stats.candidates_with_final_rate}")
            print(f"   - Average final rate: ${stats.avg_final_rate:.2f}" if stats.avg_final_rate else "   - Average final rate: N/A")
            
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        logging.error(f"Migration error: {str(e)}")
        return False

async def rollback_migration():
    """Rollback the migration (remove added columns)."""
    print("🔄 Rolling back Task 2 migration...")
    
    rollback_sql = """
    -- Remove the cost-related columns
    ALTER TABLE candidates 
    DROP COLUMN IF EXISTS rate,
    DROP COLUMN IF EXISTS margin,
    DROP COLUMN IF EXISTS infrastructure_cost,
    DROP COLUMN IF EXISTS processing_cost,
    DROP COLUMN IF EXISTS final_client_rate,
    DROP COLUMN IF EXISTS notice_period,
    DROP COLUMN IF EXISTS availability_status,
    DROP COLUMN IF EXISTS available_from,
    DROP COLUMN IF EXISTS comments,
    DROP COLUMN IF EXISTS priority_level,
    DROP COLUMN IF EXISTS shortlist_date,
    DROP COLUMN IF EXISTS last_updated;
    
    -- Drop indexes
    DROP INDEX IF EXISTS idx_candidates_final_rate;
    DROP INDEX IF EXISTS idx_candidates_status_rate;
    """
    
    try:
        async with engine.begin() as connection:
            await connection.execute(text(rollback_sql))
        print("✅ Rollback completed successfully")
        return True
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

async def test_cost_calculations_in_db():
    """Test cost calculations with real database records."""
    print("\n🧪 Testing Cost Calculations in Database")
    print("-" * 40)
    
    # Insert test candidates with cost data
    test_data_sql = """
    -- Insert or update test candidates with cost data
    INSERT INTO candidates (
        job_id, vendor_id, name, email, status,
        rate, margin, infrastructure_cost, processing_cost, final_client_rate,
        last_updated
    ) VALUES 
    (1, 1, 'Test Candidate 1', 'test1@example.com', 'Shortlisted',
     50.0, 10.0, 5.0, 5.0, 70.0, NOW()),
    (1, 1, 'Test Candidate 2', 'test2@example.com', 'Shortlisted', 
     100.0, 20.0, 8.0, 12.0, 140.0, NOW()),
    (1, 1, 'Test Candidate 3', 'test3@example.com', 'Shortlisted',
     75.0, 0.0, 0.0, 0.0, 75.0, NOW())
    ON CONFLICT (email) DO UPDATE SET
        rate = EXCLUDED.rate,
        margin = EXCLUDED.margin,
        infrastructure_cost = EXCLUDED.infrastructure_cost,
        processing_cost = EXCLUDED.processing_cost,
        final_client_rate = EXCLUDED.final_client_rate,
        last_updated = NOW();
    """
    
    # Verify calculations
    verify_sql = """
    SELECT 
        name,
        rate,
        margin,
        infrastructure_cost,
        processing_cost,
        final_client_rate,
        (rate + margin + infrastructure_cost + processing_cost) as calculated_rate,
        (final_client_rate = rate + margin + infrastructure_cost + processing_cost) as calculation_correct
    FROM candidates 
    WHERE name LIKE 'Test Candidate%'
    ORDER BY name;
    """
    
    try:
        async with engine.begin() as connection:
            # Insert test data
            await connection.execute(text(test_data_sql))
            print("✅ Test candidates inserted")
            
            # Verify calculations
            result = await connection.execute(text(verify_sql))
            test_candidates = result.fetchall()
            
            print("\n📊 Cost Calculation Verification:")
            for candidate in test_candidates:
                status = "✅" if candidate.calculation_correct else "❌"
                print(f"{status} {candidate.name}:")
                print(f"   Rate: ${candidate.rate}, Margin: ${candidate.margin}")
                print(f"   Infrastructure: ${candidate.infrastructure_cost}, Processing: ${candidate.processing_cost}")
                print(f"   Stored Final Rate: ${candidate.final_client_rate}")
                print(f"   Calculated Rate: ${candidate.calculated_rate}")
                print(f"   Calculation Correct: {candidate.calculation_correct}")
                print()
            
            all_correct = all(c.calculation_correct for c in test_candidates)
            if all_correct:
                print("✅ All cost calculations are correct!")
            else:
                print("❌ Some calculations are incorrect!")
                
            return all_correct
            
    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1 and sys.argv[1] == "rollback":
            success = await rollback_migration()
        else:
            success = await run_migration()
            if success:
                await test_cost_calculations_in_db()
        
        return success
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1)