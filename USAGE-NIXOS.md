# Using web-noise on NixOS with Home Manager

The web-noise package includes a Home Manager module for declarative configuration.

## Quick Start

### Basic Usage (Manual Config)

Add to your home configuration:

```nix
{
  cli.web-noise.enable = true;
}
```

This will:
- Install the `web-noise` package
- Create config at `~/.config/web-noise/config.json` with sensible defaults
- Copy browser profiles and example config for reference

Run manually:
```bash
web-noise -c ~/.config/web-noise/config.json -u 2 -t 3600
```

### Declarative Configuration

Customize the configuration in your home.nix:

```nix
{
  cli.web-noise = {
    enable = true;

    # Configuration options
    maxDepth = 15;
    minSleep = 3;
    maxSleep = 8;
    timeout = 7200;  # 2 hours, or false for unlimited

    rootUrls = [
      "https://www.wikipedia.org"
      "https://www.reddit.com"
      "https://news.ycombinator.com"
      "https://www.bbc.com/news"
      "https://arstechnica.com"
      # Add your own URLs
    ];

    blacklistedUrls = [
      # File extensions
      ".css"
      ".ico"
      ".png"
      ".jpg"
      ".pdf"
      # Tracking/URL shorteners
      "bit.ly"
      "t.co"
      # Add your own patterns
    ];
  };
}
```

### Enable as a Service

#### Continuous Mode (Always Running)

Run web-noise continuously in the background:

```nix
{
  cli.web-noise = {
    enable = true;

    # Optional: customize config
    timeout = false;  # Run indefinitely
    maxDepth = 12;

    # Enable systemd service (continuous mode)
    service = {
      enable = true;
      users = 3;              # Simulate 3 concurrent users
      logLevel = "info";      # debug, info, warning, or error
      serviceTimeout = 0;     # Run indefinitely
    };
  };
}
```

#### Timer Mode (Periodic Execution) - **Recommended**

Run web-noise periodically with randomized timing for more realistic behavior:

```nix
{
  cli.web-noise = {
    enable = true;

    service = {
      enable = true;
      users = 2;
      logLevel = "info";

      # Enable timer for periodic execution
      timer = {
        enable = true;                     # Enable periodic mode
        interval = "30min";                # Run every 30 minutes
        randomizedDelay = "5min";          # Add 0-5min random delay
        runDuration = 600;                 # Run for 10 minutes each time
        persistent = true;                 # Catch up after sleep/reboot
      };
    };
  };
}
```

**How Timer Mode Works:**
- **Start time randomization:** Runs every `interval` (e.g., 30 min) + random delay of 0 to `randomizedDelay` (e.g., 0-5 min)
- **Runtime randomization:** Each run lasts for `runDuration` ± `runDurationVariance` seconds (random per run)
- **Example with defaults:**
  - Starts every: 30-35 minutes (random)
  - Runs for: 7-13 minutes (random per run)
  - Result: Highly irregular pattern that mimics real browsing behavior
- **More realistic** than continuous operation or fixed intervals - no predictable patterns

**Randomization Examples:**
```nix
# Default (recommended): Every 30-35min, run for 7-13min
timer = {
  enable = true;
  interval = "30min";
  randomizedDelay = "5min";
  runDuration = 600;
  runDurationVariance = 180;  # ±3 minutes
};

# Very random: Every 30-40min, run for 5-15min
timer = {
  enable = true;
  interval = "30min";
  randomizedDelay = "10min";
  runDuration = 600;
  runDurationVariance = 300;  # ±5 minutes
};

# Frequent short bursts: Every 15-20min, run for 2-6min
timer = {
  enable = true;
  interval = "15min";
  randomizedDelay = "5min";
  runDuration = 240;  # 4 minutes base
  runDurationVariance = 120;  # ±2 minutes
};

# Long sessions: Every 1-2h, run for 15-35min
timer = {
  enable = true;
  interval = "1h";
  randomizedDelay = "1h";
  runDuration = 1500;  # 25 minutes base
  runDurationVariance = 600;  # ±10 minutes
};

# No runtime randomization (still random start times)
timer = {
  enable = true;
  interval = "30min";
  randomizedDelay = "5min";
  runDuration = 600;
  runDurationVariance = 0;  # Disabled
};
```

After rebuilding:
```bash
# For continuous mode:
systemctl --user status web-noise
journalctl --user -u web-noise -f

# For timer mode:
systemctl --user status web-noise.timer       # Check timer status
systemctl --user list-timers --all web-noise  # See when next run is scheduled
journalctl --user -u web-noise -f              # View logs (shows random runtime each run)

# Manually trigger a run (timer mode):
systemctl --user start web-noise.service

# Stop/start timer:
systemctl --user stop web-noise.timer
systemctl --user start web-noise.timer
```

### Custom Browser Profiles

To use your own browser profile collection:

```nix
{
  cli.web-noise = {
    enable = true;
    browserProfilesFile = ./my-custom-profiles.json;

    service.enable = true;
  };
}
```

### With Impermanence

The module automatically detects and integrates with system-wide impermanence:

```nix
{
  cli.web-noise = {
    enable = true;
    enablePersistence = true;  # Default: true if impermanence is enabled system-wide

    service.enable = true;
  };
}
```

This ensures your web-noise configuration persists across reboots on ephemeral filesystems.

## Module Options Reference

### Basic Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable` | bool | false | Enable web-noise |
| `package` | package | `pkgs.web-noise` | Package to use |
| `enablePersistence` | bool | auto-detected | Persist config with impermanence |

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `maxDepth` | int | 10 | Max links to follow from each root |
| `minSleep` | int | 2 | Min sleep between requests (seconds) |
| `maxSleep` | int | 5 | Max sleep between requests (seconds) |
| `timeout` | int\|bool | 3600 | Total runtime (seconds) or false for unlimited |
| `rootUrls` | list of strings | (10 URLs) | Starting URLs |
| `blacklistedUrls` | list of strings | (20+ patterns) | URL patterns to avoid |
| `userAgents` | list of strings | (7 agents) | User-Agent strings to choose from |
| `browserProfilesFile` | null\|path | null | Custom browser profiles JSON |

### Service Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `service.enable` | bool | false | Enable systemd user service |
| `service.users` | int | 2 | Concurrent simulated users |
| `service.logLevel` | enum | "info" | Logging level (debug\|info\|warning\|error) |
| `service.serviceTimeout` | int\|bool | 0 | Service timeout (0 = infinite for continuous mode) |

### Timer Options (for periodic execution)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `service.timer.enable` | bool | false | Enable periodic timer mode (recommended) |
| `service.timer.interval` | string | "30min" | How often to run (systemd time span) |
| `service.timer.randomizedDelay` | string | "5min" | Random start delay (0 to this value) |
| `service.timer.runDuration` | int | 600 | Base duration for each run (seconds) |
| `service.timer.runDurationVariance` | int | 180 | Random runtime variance (±seconds, per run) |
| `service.timer.persistent` | bool | true | Catch up after sleep/reboot |

## Configuration File Location

The generated config is stored at:
```
~/.config/web-noise/config.json
```

You can also find the example config and browser profiles there for reference:
```
~/.config/web-noise/config.example.json
~/.config/web-noise/browser_profiles.json
```

## Examples

### Minimal Setup

```nix
{
  cli.web-noise.enable = true;
}
```

### Conservative (Low Resource Usage) - Timer Mode

```nix
{
  cli.web-noise = {
    enable = true;
    minSleep = 5;
    maxSleep = 15;
    maxDepth = 5;

    service = {
      enable = true;
      users = 1;  # Single user only

      timer = {
        enable = true;
        interval = "1h";          # Run every hour
        randomizedDelay = "30min"; # Plus 0-30min random
        runDuration = 300;        # 5 minutes per session
      };
    };
  };
}
```

### Aggressive (High Traffic Generation)

```nix
{
  cli.web-noise = {
    enable = true;
    minSleep = 1;
    maxSleep = 3;
    maxDepth = 20;

    service = {
      enable = true;
      users = 5;  # 5 concurrent users
      logLevel = "warning";  # Reduce log noise
    };
  };
}
```

### Realistic Timing - Every ~30 Minutes

```nix
{
  cli.web-noise = {
    enable = true;

    service = {
      enable = true;
      users = 2;

      timer = {
        enable = true;
        interval = "30min";           # Base interval: 30 minutes
        randomizedDelay = "5min";      # Start time: +0-5 minutes random
        runDuration = 600;             # Base runtime: 10 minutes
        runDurationVariance = 180;     # Runtime variance: ±3 minutes
        # Result: Starts every 30-35min, runs for 7-13min (both random)
      };
    };
  };
}
```

### Privacy-Focused News Sites

```nix
{
  cli.web-noise = {
    enable = true;

    rootUrls = [
      "https://www.eff.org"
      "https://www.techdirt.com"
      "https://www.schneier.com"
      "https://krebsonsecurity.com"
      "https://arstechnica.com/security"
      "https://www.bleepingcomputer.com"
    ];

    service = {
      enable = true;
      timer.enable = true;  # Use timer mode
    };
  };
}
```

### Run Only During Work Hours (with cron)

Instead of a persistent service, use a cron-like timer:

```nix
{
  cli.web-noise.enable = true;

  # Run for 1 hour, 3 times per day during work hours
  systemd.user.timers.web-noise = {
    Unit.Description = "Web Noise Generator Timer";
    Timer = {
      OnCalendar = ["09:00" "13:00" "17:00"];
      Persistent = true;
    };
    Install.WantedBy = ["timers.target"];
  };

  systemd.user.services.web-noise-timed = {
    Unit.Description = "Web Noise Generator (Timed)";
    Service = {
      Type = "oneshot";
      ExecStart = "${pkgs.web-noise}/bin/web-noise -c ${config.xdg.configHome}/web-noise/config.json -u 2 -t 3600 -l info";
    };
  };
}
```

## Troubleshooting

### Service won't start

Check status and logs:
```bash
systemctl --user status web-noise
journalctl --user -u web-noise -n 50
```

### Config changes not taking effect

Rebuild home-manager:
```bash
home-manager switch --flake .
# or
nh home switch .
```

Then restart the service:
```bash
systemctl --user restart web-noise
```

### High resource usage

Reduce concurrent users and increase sleep times:
```nix
{
  cli.web-noise = {
    enable = true;
    minSleep = 10;
    maxSleep = 20;
    service.users = 1;
  };
}
```

### Want to temporarily disable

```bash
systemctl --user stop web-noise
systemctl --user disable web-noise
```

Or in config:
```nix
{
  cli.web-noise.service.enable = false;
}
```
