# Docker Down

## Overview

Stop Docker services and clean up containers.

## Steps

1. **Stop Docker Services**
   - Run `uv run docker down`
   - Wait for services to stop
   - Verify containers are stopped
   - Check cleanup completed

2. **Verify Cleanup**
   - Check containers are removed
   - Verify volumes are handled correctly
   - Check for any remaining processes
   - Ensure clean shutdown

## Notes

- This stops all Docker services
- Database data may be lost if using default volumes
- Use with caution if you have important data

## Checklist

- [ ] Docker services stopped
- [ ] Containers removed
- [ ] Cleanup completed
- [ ] No remaining processes

## See Also

- Related command: `/docker-up`
- Related command: `/setup-project`
