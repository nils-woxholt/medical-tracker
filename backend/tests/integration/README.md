# Migration Rollback Testing

This directory contains integration tests for database migration rollback functionality.

## Test Files

- `test_migrations.py`: Comprehensive migration rollback tests ensuring data integrity and schema consistency

## Running the Tests

### Prerequisites

1. Ensure Alembic is configured and migrations exist
2. Test database permissions (ability to create/drop test databases)
3. Required dependencies installed: `pytest`, `sqlalchemy`, `alembic`

### Running Tests

```bash
# Run all migration tests
cd backend
pytest tests/integration/test_migrations.py -v

# Run specific test class
pytest tests/integration/test_migrations.py::TestMigrationRollback -v

# Run with detailed output
pytest tests/integration/test_migrations.py -v -s

# Run performance tests separately
pytest tests/integration/test_migrations.py::TestMigrationPerformance -v
```

### Manual Testing

For debugging and manual verification:

```bash
cd backend
python tests/integration/test_migrations.py manual
```

## Test Coverage

### Schema Integrity Tests

- ✅ Migration rollback preserves schema structure  
- ✅ Forward/backward migration cycles maintain consistency
- ✅ Migration idempotency (safe re-application)
- ✅ Dependency chain validation

### Data Integrity Tests

- ✅ Data preservation during rollback operations
- ✅ Foreign key constraint handling
- ✅ Large dataset migration performance
- ✅ Error recovery scenarios

### Production Readiness Tests

- ✅ Migration dependency validation
- ✅ Performance benchmarking  
- ✅ Resource usage monitoring
- ✅ Error handling and recovery

## Test Database Isolation

Each test uses an isolated database to prevent interference:

- SQLite: Temporary files in system temp directory
- PostgreSQL/MySQL: Separate test database with unique naming

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

- No external dependencies beyond database
- Automatic cleanup of test resources
- Comprehensive error reporting
- Performance regression detection

## Troubleshooting

### Common Issues

1. **Database Permission Errors**
   - Ensure database user has CREATE DATABASE privileges
   - For SQLite, ensure write permissions to temp directory

2. **Migration Not Found Errors**
   - Verify Alembic configuration in `alembic.ini`
   - Check migration files exist in `alembic/versions/`
   - Ensure `DATABASE_URL` environment variable is set correctly

3. **Test Timeout Issues**
   - Adjust performance test thresholds in `test_migrations.py`
   - Check database performance and connection settings

### Debug Mode

Run tests with maximum verbosity:

```bash
pytest tests/integration/test_migrations.py -vvs --tb=long
```

### Performance Monitoring

The tests include performance benchmarks that will fail if migrations take too long:

- Migration time threshold: 30 seconds
- Rollback time threshold: 30 seconds  
- Large dataset: 1000+ records

Adjust thresholds in the test file if needed for your environment.