#!/usr/bin/env python3
"""
Web Traffic Noise Generator
Generates realistic random web traffic to obfuscate browsing patterns.
Supports multiple concurrent simulated users with real browser profiles.
"""

import argparse
import datetime
import json
import logging
import random
import re
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from urllib3.exceptions import LocationParseError


class NoiseGenerator:
    """Simulates a single user browsing the web with a specific browser profile"""

    def __init__(self, config: Dict, browser_profiles: List[Dict], user_id: int = 0):
        self.config = config
        self.user_id = user_id
        self.links: List[str] = []
        self.start_time: Optional[datetime.datetime] = None
        self.session = requests.Session()  # Maintain session for cookies
        self.logger = logging.getLogger(f"User-{user_id}")

        # Pick a random browser profile and stick with it
        self.browser_profile = random.choice(browser_profiles)
        self.user_agent = random.choice(self.config["user_agents"])
        self.logger.info(f"Using profile: {self.browser_profile['name']}")

    class CrawlerTimedOut(Exception):
        """Raised when the specified timeout is exceeded"""
        pass

    def _get_headers(self) -> Dict[str, str]:
        """
        Constructs HTTP headers based on the browser profile
        """
        # Start with profile headers
        headers = dict(self.browser_profile['headers'])

        # Add User-Agent from the user agent list
        headers['User-Agent'] = self.user_agent

        # Add Connection header for keep-alive
        headers['Connection'] = 'keep-alive'

        # Remove None values (represents headers not present in this browser)
        return {k: v for k, v in headers.items() if v is not None}

    def _request(self, url: str) -> requests.Response:
        """
        Sends a GET request using the browser profile headers
        """
        headers = self._get_headers()
        response = self.session.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )
        return response

    @staticmethod
    def _normalize_link(link: str, root_url: str) -> Optional[str]:
        """Normalizes links to absolute URLs"""
        try:
            parsed_url = urlparse(link)
        except ValueError:
            return None

        parsed_root_url = urlparse(root_url)

        # '//' means keep the current protocol
        if link.startswith("//"):
            return f"{parsed_root_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # Relative path
        if not parsed_url.scheme:
            return urljoin(root_url, link)

        return link

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if a URL is valid"""
        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, url) is not None

    def _is_blacklisted(self, url: str) -> bool:
        """Checks if a URL is blacklisted"""
        return any(blacklisted in url for blacklisted in self.config["blacklisted_urls"])

    def _should_accept_url(self, url: str) -> bool:
        """Filters URL based on validity and blacklist"""
        return url and self._is_valid_url(url) and not self._is_blacklisted(url)

    def _extract_urls(self, body: bytes, root_url: str) -> List[str]:
        """Extracts links from a web page"""
        pattern = r"href=[\"'](?!#)(.*?)[\"'].*?"
        urls = re.findall(pattern, str(body))

        normalized_urls = [self._normalize_link(url, root_url) for url in urls]
        filtered_urls = [url for url in normalized_urls if self._should_accept_url(url)]

        return filtered_urls

    def _remove_and_blacklist(self, link: str):
        """Removes a link and blacklists it"""
        if link not in self.config['blacklisted_urls']:
            self.config['blacklisted_urls'].append(link)
        if link in self.links:
            self.links.remove(link)

    def _random_sleep(self):
        """
        Sleep for a realistic random duration to simulate human behavior
        """
        base_sleep = random.uniform(self.config["min_sleep"], self.config["max_sleep"])

        # Simulate human reading/thinking patterns
        # 10% chance of long pause (reading article, distraction)
        if random.random() < 0.1:
            base_sleep *= random.uniform(2, 5)
        # 5% chance of quick clicking (scanning pages)
        elif random.random() < 0.05:
            base_sleep *= 0.5

        time.sleep(base_sleep)

    def _browse_from_links(self, max_depth: int):
        """
        Iteratively browse links (non-recursive to avoid stack overflow)
        """
        depth = 0

        while depth < max_depth and self.links:
            if self._is_timeout_reached():
                raise self.CrawlerTimedOut

            random_link = random.choice(self.links)
            try:
                self.logger.info(f"Visiting (depth {depth}): {random_link[:80]}...")
                response = self._request(random_link)
                sub_links = self._extract_urls(response.content, random_link)

                self._random_sleep()

                if len(sub_links) > 1:
                    # Simulate realistic browsing: don't follow every link
                    # Pick a random subset
                    num_links = min(len(sub_links), random.randint(5, 25))
                    self.links = random.sample(sub_links, num_links)
                    depth += 1
                else:
                    # Dead end, try another link from current list
                    self._remove_and_blacklist(random_link)

            except requests.exceptions.Timeout:
                self.logger.debug(f"Timeout on {random_link[:60]}")
                self._remove_and_blacklist(random_link)
            except requests.exceptions.RequestException as e:
                self.logger.debug(f"Request error on {random_link[:60]}: {type(e).__name__}")
                self._remove_and_blacklist(random_link)
            except MemoryError:
                self.logger.warning(f"Memory error on {random_link[:60]}, skipping")
                self._remove_and_blacklist(random_link)
            except Exception as e:
                self.logger.warning(f"Unexpected error on {random_link[:60]}: {type(e).__name__}")
                self._remove_and_blacklist(random_link)

    def _is_timeout_reached(self) -> bool:
        """Determines whether the specified timeout has been reached"""
        if self.config["timeout"] is False:
            return False
        end_time = self.start_time + datetime.timedelta(seconds=self.config["timeout"])
        return datetime.datetime.now() >= end_time

    def run(self):
        """Main crawling loop for this simulated user"""
        self.start_time = datetime.datetime.now()
        self.logger.info(f"Starting noise generation")

        try:
            while True:
                if self._is_timeout_reached():
                    self.logger.info("Timeout reached, stopping")
                    break

                url = random.choice(self.config["root_urls"])
                try:
                    self.logger.info(f"Starting from root: {url}")
                    response = self._request(url)
                    self.links = self._extract_urls(response.content, url)

                    if self.links:
                        self.logger.debug(f"Found {len(self.links)} links")
                        self._browse_from_links(self.config['max_depth'])
                    else:
                        self.logger.debug(f"No links found at {url}")

                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"Error connecting to {url}: {type(e).__name__}")

                except LocationParseError:
                    self.logger.warning(f"Parse error on {url}")

                except self.CrawlerTimedOut:
                    self.logger.info("Timeout exceeded, exiting")
                    break

                # Random pause between root URL visits (simulate navigating to new site)
                time.sleep(random.uniform(2, 8))

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            self.session.close()


class MultiUserNoiseGenerator:
    """Manages multiple concurrent simulated users"""

    def __init__(self, config: Dict, browser_profiles: List[Dict], num_users: int = 1):
        self.config = config
        self.browser_profiles = browser_profiles
        self.num_users = num_users
        self.threads: List[threading.Thread] = []
        self.logger = logging.getLogger("MultiUser")

    def _user_worker(self, user_id: int):
        """Worker function for each user thread"""
        # Create a deep copy of config for each user to avoid race conditions
        user_config = json.loads(json.dumps(self.config))
        user = NoiseGenerator(user_config, self.browser_profiles, user_id)
        user.run()

    def run(self):
        """Start all simulated users"""
        self.logger.info(f"Starting {self.num_users} simulated user(s)")

        # Start all user threads with staggered start times
        for i in range(self.num_users):
            thread = threading.Thread(
                target=self._user_worker,
                args=(i,),
                daemon=True,
                name=f"User-{i}"
            )
            self.threads.append(thread)
            thread.start()

            # Stagger starts (2-5 seconds apart) to be more realistic
            if i < self.num_users - 1:  # Don't sleep after last thread
                time.sleep(random.uniform(2, 5))

        self.logger.info("All users started")

        # Wait for all threads to complete
        try:
            for thread in self.threads:
                thread.join()
        except KeyboardInterrupt:
            self.logger.info("Interrupted, waiting for threads to finish...")
            # Give threads some time to clean up
            for thread in self.threads:
                thread.join(timeout=5)


def load_json_file(file_path: Path) -> Dict:
    """Load and parse a JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description='Generate web traffic noise for privacy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--log', '-l',
        type=str,
        choices=['debug', 'info', 'warning', 'error'],
        help='Logging level',
        default='info'
    )
    parser.add_argument(
        '--config', '-c',
        required=True,
        type=Path,
        help='Path to config JSON file'
    )
    parser.add_argument(
        '--profiles', '-p',
        type=Path,
        help='Path to browser profiles JSON file',
        default=None
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        help='Duration to run (seconds), 0 for infinite',
        default=None
    )
    parser.add_argument(
        '--users', '-u',
        type=int,
        help='Number of concurrent simulated users',
        default=1
    )

    args = parser.parse_args()

    # Setup logging
    level = getattr(logging, args.log.upper())
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Load config
    if not args.config.exists():
        logging.error(f"Config file not found: {args.config}")
        return 1

    config = load_json_file(args.config)

    # Load browser profiles
    if args.profiles:
        profiles_path = args.profiles
    else:
        # Default to browser_profiles.json in same directory as this script
        profiles_path = Path(__file__).parent / 'browser_profiles.json'

    if not profiles_path.exists():
        logging.error(f"Browser profiles file not found: {profiles_path}")
        return 1

    profiles_data = load_json_file(profiles_path)
    browser_profiles = profiles_data['profiles']

    logging.info(f"Loaded {len(browser_profiles)} browser profiles")

    # Override timeout if specified
    if args.timeout is not None:
        config['timeout'] = args.timeout if args.timeout > 0 else False

    # Run noise generator
    generator = MultiUserNoiseGenerator(config, browser_profiles, args.users)
    generator.run()

    logging.info("Noise generation complete")
    return 0


if __name__ == '__main__':
    exit(main())
