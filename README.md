# web-noise

Generate realistic web traffic noise for privacy by simulating human browsing patterns.

## Motivation

Traffic analysis is more common than many might think. In an era where AI is increasingly deployed for surveillance and data analysis, traffic analysis has become easier, cheaper, and more pervasive. Mass surveillance programs routinely employ dragnet approaches to monitor and analyze browsing patterns of entire populations.

**The solution? Create noise.**

By generating realistic, random web traffic alongside your real browsing, you make it significantly harder and more resource-intensive for adversaries to identify the signal (your actual browsing) within the noise. This tool helps level the playing field against automated traffic analysis systems.

Remember: Privacy is not about having something to hide—it's about having something to protect.

## Features

- **Multi-user simulation**: Run multiple concurrent simulated users (configurable)
- **Real browser profiles**: Uses authentic HTTP headers from Chrome, Firefox, Safari, and Edge
- **Human-like behavior**: Variable sleep times, random link selection, realistic reading patterns
- **Session management**: Maintains cookies per simulated user for authenticity
- **Configurable**: Customize browsing depth, timeout, root URLs, and blacklists

## Installation

### Debian/Ubuntu (APT-based systems)

```bash
# Install Python 3 and pip
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Clone the repository
git clone https://github.com/aciddemon/web-noise.git
cd web-noise

# Install using pip (recommended: use virtual environment)
python3 -m venv venv
source venv/bin/activate
pip install .

# Or install system-wide (not recommended)
sudo pip3 install .
```

### Fedora/RHEL/CentOS (DNF/YUM-based systems)

```bash
# Install Python 3 and pip
sudo dnf install python3 python3-pip

# Clone the repository
git clone https://github.com/aciddemon/web-noise.git
cd web-noise

# Install using pip (recommended: use virtual environment)
python3 -m venv venv
source venv/bin/activate
pip install .

# Or install system-wide (not recommended)
sudo pip3 install .
```

### Other Linux Distributions / macOS

```bash
# Ensure Python 3.6+ is installed
python3 --version

# Clone the repository
git clone https://github.com/aciddemon/web-noise.git
cd web-noise

# Install using pip with virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install .
```

### NixOS / Nix Package Manager

Add to your NixOS configuration:

```nix
# System-wide installation
environment.systemPackages = with pkgs; [
  web-noise
];

# Or via Home Manager
home.packages = with pkgs; [
  web-noise
];
```

Then rebuild:

```bash
sudo nixos-rebuild switch --flake .
# or
nh os switch .
```

## Usage

### Quick Start

1. **Copy the example configuration:**

```bash
# If installed via pip/venv
cp config.example.json ~/web-noise-config.json

# If installed on NixOS
cp /nix/store/$(nix-build '<nixpkgs>' -A web-noise)/share/web-noise/config.example.json ~/web-noise-config.json
```

2. **Run with default settings** (1 user, 1 hour timeout):

```bash
web-noise -c ~/web-noise-config.json
```

### Command-Line Options

```bash
# Show help
web-noise --help

# Run with 3 concurrent simulated users
web-noise -c ~/web-noise-config.json --users 3

# Run for 2 hours (7200 seconds)
web-noise -c ~/web-noise-config.json --timeout 7200

# Run indefinitely
web-noise -c ~/web-noise-config.json --timeout 0

# Use custom browser profiles
web-noise -c ~/web-noise-config.json --profiles ./browser_profiles.json

# Enable debug logging
web-noise -c ~/web-noise-config.json --log debug

# Combine options: 5 users, 4 hours, debug mode
web-noise -c ~/config.json -u 5 -t 14400 -l debug
```

### Running in Background

```bash
# Using nohup (will continue running after logout)
nohup web-noise -c ~/config.json -u 2 -t 0 > ~/web-noise.log 2>&1 &

# Using screen
screen -S webnoise
web-noise -c ~/config.json -u 2 -t 0
# Press Ctrl+A, then D to detach

# Using tmux
tmux new -s webnoise
web-noise -c ~/config.json -u 2 -t 0
# Press Ctrl+B, then D to detach
```

## Configuration

### Example config.json

```json
{
  "max_depth": 10,
  "min_sleep": 2,
  "max_sleep": 5,
  "timeout": 3600,
  "root_urls": [
    "https://www.wikipedia.org",
    "https://www.reddit.com",
    "https://news.ycombinator.com",
    "https://www.bbc.com/news",
    "https://www.theguardian.com",
    "https://www.nytimes.com",
    "https://arstechnica.com",
    "https://www.nature.com",
    "https://www.sciencedaily.com",
    "https://github.com/explore"
  ],
  "blacklisted_urls": [
    "https://t.co",
    "t.umblr.com",
    "bit.ly",
    ".css",
    ".ico",
    ".json",
    ".png",
    ".jpg",
    ".gif",
    ".pdf",
    ".zip"
  ],
  "user_agents": [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
  ]
}
```

### Configuration Options

- **max_depth**: Maximum number of links to follow from each root URL (default: 10)
- **min_sleep**: Minimum sleep time between requests in seconds (default: 2)
- **max_sleep**: Maximum sleep time between requests in seconds (default: 5)
- **timeout**: Total runtime in seconds, or `false` for unlimited (default: 3600)
- **root_urls**: List of starting URLs to begin browsing from
- **blacklisted_urls**: URL patterns to avoid (file extensions, tracking domains, etc.)
- **user_agents**: List of User-Agent strings to randomly select from

### Browser Profiles

Browser profiles contain real HTTP headers from actual browsers collected from https://requestheaders.dev/.

The package includes **15 authentic profiles** from:

- **Chrome 106/107** (Windows, macOS, Linux)
- **Firefox 106/107** (Windows, macOS, Linux)
- **Safari 15/16** (macOS, iOS)
- **Edge 105/106** (Windows, macOS)

Each profile includes appropriate headers like:

- `Accept` - Content type preferences
- `Accept-Language` - Various locales (en-US, en-GB, de-DE, fr-FR, es-ES, it-IT, nl-NL, en-AU)
- `Accept-Encoding` - Compression support (gzip, deflate, br)
- `DNT` - Do Not Track header (present in some profiles, absent in others - realistic variation)
- `Sec-Ch-Ua` headers - Chromium-based browser hints
- `Sec-Fetch-*` headers - Fetch metadata

The tool randomly selects one profile per simulated user and maintains it consistently for the entire session (realistic behavior).

## Running as a Service

### systemd (Linux)

Create `/etc/systemd/system/web-noise.service`:

```ini
[Unit]
Description=Web Traffic Noise Generator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=aciddemon
WorkingDirectory=/home/aciddemon
ExecStart=/usr/local/bin/web-noise -c /home/aciddemon/.config/web-noise/config.json -u 2 -t 0
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable web-noise
sudo systemctl start web-noise
sudo systemctl status web-noise
```

### NixOS systemd service

```nix
# In your NixOS configuration
systemd.user.services.web-noise = {
  description = "Web Traffic Noise Generator";
  wantedBy = [ "default.target" ];
  after = [ "network-online.target" ];

  serviceConfig = {
    Type = "simple";
    ExecStart = "${pkgs.web-noise}/bin/web-noise -c /home/acid/.config/web-noise/config.json -u 2 -t 0";
    Restart = "on-failure";
    RestartSec = "30s";
  };
};
```

### cron (Alternative)

Add to crontab (`crontab -e`):

```cron
# Run every 4 hours for 3 hours
0 */4 * * * /usr/local/bin/web-noise -c /home/aciddemon/web-noise-config.json -u 2 -t 10800 >> /home/aciddemon/web-noise.log 2>&1
```

## Privacy Considerations

- This tool generates **random** web traffic, not **targeted** browsing
- Traffic patterns may still be distinguishable from real human browsing under sophisticated analysis
- Use in combination with other privacy tools (VPN, Tor, etc.) for best results
- Consider network bandwidth and CPU usage when running multiple concurrent users
- Some websites may rate-limit or block automated traffic
- Does not click ads or perform actions that could affect analytics or cost website owners money

## Troubleshooting

### "Config file not found"

Ensure the path to your config file is correct:

```bash
ls -la ~/web-noise-config.json
web-noise -c $(pwd)/config.json  # Use absolute path
```

### "Browser profiles file not found"

The default profiles are bundled with the package at `browser_profiles.json`. Only specify `--profiles` if you want to use custom profiles:

```bash
web-noise -c config.json --profiles ./custom_profiles.json
```

### "ModuleNotFoundError: No module named 'requests'"

Install dependencies:

```bash
pip install requests urllib3
# Or reinstall the package
pip install --force-reinstall .
```

### High CPU/Memory usage

- Reduce the number of concurrent users: `--users 1`
- Increase sleep times in config.json: `"min_sleep": 5, "max_sleep": 10`
- Reduce max_depth: `"max_depth": 5`

### Getting blocked by websites

Add aggressive rate-limiting domains to `blacklisted_urls`:

```json
"blacklisted_urls": [
  "aggressive-site.com",
  "another-blocker.net"
]
```

### Permission denied on Linux

If installed system-wide without sudo, install in user space:

```bash
pip install --user .
```

## Requirements

- **Python**: 3.6 or higher
- **Dependencies**:
  - `requests` - HTTP library
  - `urllib3` - URL parsing and validation

## Technical Details

- **Language**: Python 3.6+
- **Dependencies**: requests, urllib3
- **Architecture**: Multi-threaded (one thread per simulated user)
- **Session handling**: Each user maintains independent session with cookies
- **Link extraction**: Regex-based HTML parsing (`href` attribute extraction)
- **URL filtering**: Blacklist-based with validity checking and normalization
- **Behavior simulation**:
  - 10% chance of long pause (2-5x base sleep) simulating reading
  - 5% chance of quick clicking (0.5x base sleep) simulating scanning
  - Random link selection from extracted URLs
  - Staggered start times for multiple users (2-5 seconds apart)

## License

MIT License

## Contributing

Contributions welcome! Please open issues or pull requests on GitHub.

## Disclaimer

This tool is for privacy research and personal use only. Users are responsible for complying with applicable laws and website terms of service. The authors are not responsible for misuse of this tool.
