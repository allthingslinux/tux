# Self-Host Troubleshooting

Common issues when self-hosting Tux and their solutions.

## Installation Issues

### Docker Issues
- **Check Docker installation** - Ensure Docker and Docker Compose are properly installed
- **Check port conflicts** - Verify ports 8080 and 5432 are not in use
- **Check disk space** - Ensure sufficient disk space for containers and data

### Manual Installation Issues
- **Check Python version** - Ensure Python 3.11+ is installed
- **Check dependencies** - Verify all required packages are installed
- **Check system requirements** - Ensure sufficient RAM and disk space

## Configuration Issues

### Environment Variables
- **Check .env file** - Verify all required environment variables are set
- **Check variable format** - Ensure variables are properly formatted
- **Check file permissions** - Verify .env file is readable by the bot

### Database Configuration
- **Check database connection** - Verify PostgreSQL is running and accessible
- **Check database credentials** - Ensure database username/password are correct
- **Check database permissions** - Verify the database user has necessary permissions

## Runtime Issues

### Bot Not Starting
- **Check logs** - Examine bot logs for error messages
- **Check dependencies** - Ensure all required services are running
- **Check configuration** - Verify configuration files are valid

### Performance Issues
- **Check system resources** - Monitor CPU, RAM, and disk usage
- **Check database performance** - Verify database is not overloaded
- **Check network connectivity** - Ensure stable internet connection

## Getting Help

If you can't resolve your issue:
1. Check the **[FAQ](../community/faq.md)** for common solutions
2. Join our **[Discord server](https://discord.gg/gpmSjcjQxg)** for community support
3. File an issue on **[GitHub](https://github.com/allthingslinux/tux/issues)** for bugs
