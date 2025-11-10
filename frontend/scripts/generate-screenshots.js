#!/usr/bin/env node

/**
 * Generate placeholder screenshots for PWA
 */

const sharp = require('sharp');
const path = require('path');

const publicDir = path.join(__dirname, '..', 'public');

// Create wide screenshot (desktop/tablet)
const createWideScreenshot = () => `
<svg width="1280" height="720" viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <rect width="1280" height="720" fill="#f8fafc"/>
  <rect width="1280" height="60" fill="#3b82f6"/>
  <text x="640" y="38" text-anchor="middle" font-family="Arial, sans-serif"
    font-size="24" font-weight="bold" fill="white">TutorMax Dashboard</text>
  <rect x="40" y="100" width="580" height="280" rx="8" fill="white" stroke="#e2e8f0" stroke-width="2"/>
  <text x="330" y="250" text-anchor="middle" font-size="20" fill="#64748b">Performance Analytics</text>
  <rect x="660" y="100" width="580" height="280" rx="8" fill="white" stroke="#e2e8f0" stroke-width="2"/>
  <text x="950" y="250" text-anchor="middle" font-size="20" fill="#64748b">Real-time Metrics</text>
  <rect x="40" y="420" width="1200" height="260" rx="8" fill="white" stroke="#e2e8f0" stroke-width="2"/>
  <text x="640" y="560" text-anchor="middle" font-size="20" fill="#64748b">Tutor Performance Overview</text>
</svg>
`;

// Create narrow screenshot (mobile)
const createNarrowScreenshot = () => `
<svg width="750" height="1334" viewBox="0 0 750 1334" xmlns="http://www.w3.org/2000/svg">
  <rect width="750" height="1334" fill="#f8fafc"/>
  <rect width="750" height="120" fill="#3b82f6"/>
  <text x="375" y="75" text-anchor="middle" font-family="Arial, sans-serif"
    font-size="32" font-weight="bold" fill="white">TutorMax</text>
  <rect x="40" y="160" width="670" height="320" rx="12" fill="white" stroke="#e2e8f0" stroke-width="3"/>
  <circle cx="375" cy="250" r="40" fill="#3b82f6" opacity="0.2"/>
  <text x="375" y="340" text-anchor="middle" font-size="24" fill="#64748b">Performance</text>
  <text x="375" y="370" text-anchor="middle" font-size="24" fill="#64748b">Dashboard</text>
  <rect x="40" y="520" width="670" height="280" rx="12" fill="white" stroke="#e2e8f0" stroke-width="3"/>
  <text x="375" y="670" text-anchor="middle" font-size="24" fill="#64748b">Quick Actions</text>
  <rect x="40" y="840" width="670" height="280" rx="12" fill="white" stroke="#e2e8f0" stroke-width="3"/>
  <text x="375" y="990" text-anchor="middle" font-size="24" fill="#64748b">Recent Activity</text>
</svg>
`;

async function generateScreenshots() {
  console.log('Generating PWA screenshots...\n');

  try {
    const wideScreenshotSvg = Buffer.from(createWideScreenshot());
    await sharp(wideScreenshotSvg)
      .resize(1280, 720)
      .png({ quality: 90 })
      .toFile(path.join(publicDir, 'screenshot-1.png'));
    console.log('✓ Created wide screenshot (1280x720)');
  } catch (error) {
    console.error('✗ Failed to create wide screenshot:', error.message);
  }

  try {
    const narrowScreenshotSvg = Buffer.from(createNarrowScreenshot());
    await sharp(narrowScreenshotSvg)
      .resize(750, 1334)
      .png({ quality: 90 })
      .toFile(path.join(publicDir, 'screenshot-2.png'));
    console.log('✓ Created narrow screenshot (750x1334)');
  } catch (error) {
    console.error('✗ Failed to create narrow screenshot:', error.message);
  }

  console.log('\n✨ Screenshot generation complete!');
}

generateScreenshots().catch(console.error);
