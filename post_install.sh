#!/bin/bash
set -euo pipefail
echo "Installing chromium browser for puppeteer..."
cd node_modules/puppeteer
npm install
