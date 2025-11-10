#!/usr/bin/env node

/**
 * Generate PWA icons using Sharp
 * Creates optimized PNG icons from SVG source
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const publicDir = path.join(__dirname, '..', 'public');

// SVG icon template
const createIconSVG = (size) => `
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1d4ed8;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${size * 0.225}" fill="url(#grad)"/>
  <g transform="translate(${size * 0.5}, ${size * 0.5})">
    <circle r="${size * 0.28}" fill="none" stroke="white" stroke-width="${size * 0.05}" opacity="0.9"/>
    <path d="M${-size * 0.15} ${-size * 0.05}L${-size * 0.05} ${size * 0.1}L${size * 0.15} ${-size * 0.12}"
      stroke="white" stroke-width="${size * 0.06}" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <text x="0" y="${size * 0.38}" text-anchor="middle" font-family="Arial, sans-serif"
      font-size="${size * 0.13}" font-weight="bold" fill="white">TutorMax</text>
  </g>
</svg>
`;

async function generateIcons() {
  console.log('Generating PWA icons...\n');

  for (const size of sizes) {
    const svgBuffer = Buffer.from(createIconSVG(size));
    const outputPath = path.join(publicDir, `icon-${size}x${size}.png`);

    try {
      await sharp(svgBuffer)
        .resize(size, size)
        .png({ quality: 100, compressionLevel: 9 })
        .toFile(outputPath);

      console.log(`✓ Created ${size}x${size} icon`);
    } catch (error) {
      console.error(`✗ Failed to create ${size}x${size} icon:`, error.message);
    }
  }

  // Create favicon
  try {
    const faviconSvg = Buffer.from(createIconSVG(32));
    await sharp(faviconSvg)
      .resize(32, 32)
      .png({ quality: 100 })
      .toFile(path.join(publicDir, 'favicon.png'));
    console.log('✓ Created favicon.png');
  } catch (error) {
    console.error('✗ Failed to create favicon:', error.message);
  }

  // Create apple-touch-icon
  try {
    const appleTouchIconSvg = Buffer.from(createIconSVG(180));
    await sharp(appleTouchIconSvg)
      .resize(180, 180)
      .png({ quality: 100 })
      .toFile(path.join(publicDir, 'apple-touch-icon.png'));
    console.log('✓ Created apple-touch-icon.png');
  } catch (error) {
    console.error('✗ Failed to create apple-touch-icon:', error.message);
  }

  console.log('\n✨ Icon generation complete!');
}

generateIcons().catch(console.error);
