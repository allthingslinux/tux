# Firewall Configuration

Network security for your Tux deployment.

## UFW (Ubuntu/Debian)

### Basic Setup

```bash
# Install UFW
sudo apt install ufw

# Allow SSH (important!)
sudo ufw allow ssh

# Allow specific port
sudo ufw allow 8080/tcp comment 'Adminer (dev only)'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Recommended Rules

```bash
# Allow SSH
sudo ufw allow 22/tcp

# DENY PostgreSQL publicly (only localhost!)
# Don't run: sudo ufw allow 5432/tcp

# Allow Adminer (development only)
sudo ufw allow 8080/tcp

# For production, don't expose Adminer
```

## iptables

For advanced firewalling:

```bash
# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Drop PostgreSQL external access
sudo iptables -A INPUT -p tcp --dport 5432 -j DROP
```

## Docker Networks

Docker Compose creates isolated networks:

- Containers communicate internally
- Only exposed ports accessible from host
- No external access by default

## PostgreSQL Network Security

```conf
# In postgresql.conf
listen_addresses = 'localhost'
```

Only accept local connections.

## Related

- **[Best Practices](best-practices.md)**
- **[System Security](best-practices.md#system-security)**

---

*Complete firewall guide in progress.*
