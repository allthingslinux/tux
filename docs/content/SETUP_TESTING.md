# Tux Setup Testing Guide

This guide explains how to test and validate your Tux setup using the provided testing tools.

## 🧪 **Setup Test Script**

The `scripts/test-setup.py` script validates your configuration setup and ensures everything is working correctly.

### Running the Setup Test

```bash
# Using the Makefile target (recommended)
make test-setup

# Or directly with Python
poetry run python scripts/test-setup.py

# Or with uv
uv run python scripts/test-setup.py
```

### What the Setup Test Checks

1. **Imports** - Verifies all configuration modules can be imported
2. **Configuration** - Tests that configuration values are loaded correctly
3. **Environment Detection** - Validates environment detection and prefix selection
4. **Database Configuration** - Checks database URL configuration
5. **Feature Configs** - Tests XP, snippets, TempVC, and IRC configurations
6. **Environment Variables** - Validates .env file and key variables

### Expected Output

```
🚀 Tux Setup Test Script
==================================================
🧪 Testing imports...
✅ CONFIG imported successfully
✅ Environment module imported successfully
✅ Configuration models imported successfully

🔧 Testing configuration...
✅ Environment: dev
✅ Debug mode: False
✅ Bot name: Tux
✅ Bot version: 0.0.0
✅ Bot prefix: ~
...

📊 Test Results: 6/6 passed
🎉 All tests passed! Setup looks good.
```

---

## 📋 **Setup Test Checklist**

The `SETUP_TEST_CHECKLIST.md` file provides a comprehensive checklist for testing the complete setup process from scratch.

### When to Use the Checklist

- **New user onboarding** - Ensure setup works for first-time users
- **CI/CD validation** - Verify deployment processes work correctly
- **Environment testing** - Test setup on different systems/environments
- **Documentation validation** - Ensure docs match actual behavior

### Checklist Categories

1. **Developer Setup (Local)** - UV + Python setup
2. **Developer Setup (Docker)** - Docker development environment
3. **Production Setup** - Production Docker deployment
4. **Configuration Validation** - Environment variables and bot config
5. **Cleanup Testing** - Ensure no leftover processes/files

---

## 🔧 **Testing Different Environments**

### Development Environment

```bash
# Run setup test (automatically detects development)
make test-setup

# Expected: Context: dev, Debug: True, Prefix: ~
```

### Production Environment

```bash
# Run setup test in Docker (automatically detects production)
make prod

# Check context
python -c "from tux.shared.config.environment import get_context_name; print(f'Context: {get_context_name()}')"

# Expected: Context: prod, Debug: False
```

### Test Environment

```bash
# Run tests (automatically detects test context)
make test

# Check context during testing
python -c "from tux.shared.config.environment import get_context_name; print(f'Context: {get_context_name()}')"

# Expected: Context: test, Debug: False
```

---

## 🚨 **Troubleshooting Common Issues**

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'tux'`
**Solution**: Ensure you're in the project root and using the correct Python environment

```bash
# Check current directory
pwd  # Should be /path/to/tux

# Activate virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Run test
make test-setup
```

### Configuration Errors

**Problem**: Configuration values are missing or incorrect
**Solution**: Check your `.env` file and ensure all required variables are set

```bash
# Check .env file
cat .env

# Ensure these variables are set:
# BOT_TOKEN=your_token
# DATABASE_URL=your_db_url
```

### Database Connection Issues

**Problem**: Database URL configuration fails
**Solution**: Verify database is running and connection string is correct

```bash
# Test PostgreSQL connection
psql "postgresql://user:pass@localhost:5432/db"

# Test SQLite file permissions
touch tux.db
rm tux.db
```

---

## 📊 **Test Results Interpretation**

### All Tests Pass (6/6)
🎉 **Setup is working perfectly!**
- Configuration loads correctly
- All modules import successfully
- Environment detection works
- Database configuration is valid

### Some Tests Fail (1-5/6)
⚠️ **Setup has issues that need attention**
- Check the specific failing tests
- Review error messages for clues
- Verify configuration files
- Check system requirements

### All Tests Fail (0/6)
❌ **Major setup problem**
- Verify Python environment
- Check project structure
- Ensure dependencies are installed
- Review system requirements

---

## 🔄 **Continuous Testing**

### Pre-commit Testing

Add setup testing to your development workflow:

```bash
# Before committing changes
make test-setup
make test-quick

# Full quality check
make quality
```

### CI/CD Integration

Include setup testing in your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Test Configuration Setup
  run: make test-setup

- name: Run Tests
  run: make test
```

---

## 📝 **Customizing Tests**

### Adding New Test Cases

Edit `scripts/test-setup.py` to add new validation tests:

```python
def test_custom_feature():
    """Test custom feature configuration."""
    print("\n🔧 Testing custom feature...")
    
    from tux.shared.config import CONFIG
    
    # Add your test logic here
    print(f"✅ Custom feature: {CONFIG.CUSTOM_FEATURE}")
    
    return True

# Add to tests list
tests = [
    test_imports,
    test_configuration,
    test_custom_feature,  # Add your test
    # ... other tests
]
```

### Environment-Specific Tests

Add tests that only run in certain environments:

```python
def test_production_features():
    """Test production-specific features."""
    if CONFIG.ENV != "prod":
        print("⏭️ Skipping production tests in non-production environment")
        return True
    
    # Production-specific test logic
    return True
```

---

## 🎯 **Best Practices**

1. **Run setup tests regularly** - Especially after configuration changes
2. **Test in clean environments** - Use fresh VMs/containers for testing
3. **Document failures** - Keep notes on common issues and solutions
4. **Update checklists** - Modify checklists based on new features
5. **Automate testing** - Include setup tests in CI/CD pipelines

---

## 📚 **Additional Resources**

- **SETUP.md** - Main setup documentation
- **Database Lifecycle Guide** - Comprehensive database management and migration guide
- **env.example** - Environment variable template
- **docker-compose.yml** - Docker configuration
- **Makefile** - Available commands and targets

---

**Last Updated**: $(date)
**Version**: [Tux Version]
