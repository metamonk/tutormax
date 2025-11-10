#!/usr/bin/env node

/**
 * Simple icon generator for PWA
 * Creates placeholder SVG icons for TutorMax
 */

const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const publicDir = path.join(__dirname, '..', 'public');

// Create a simple SVG icon
function createIconSVG(size) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" rx="${size * 0.2}" fill="#3b82f6"/>
  <path d="M${size * 0.3} ${size * 0.4}L${size * 0.5} ${size * 0.6}L${size * 0.7} ${size * 0.35}"
    stroke="white" stroke-width="${size * 0.08}" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="${size * 0.5}" cy="${size * 0.5}" r="${size * 0.3}"
    stroke="white" stroke-width="${size * 0.06}" fill="none"/>
</svg>`;
}

// Generate icons
sizes.forEach(size => {
  const iconPath = path.join(publicDir, `icon-${size}x${size}.png`);
  const svgContent = createIconSVG(size);

  // For development, we'll create SVG files instead of PNG
  // In production, you should use a proper image conversion tool
  const svgPath = path.join(publicDir, `icon-${size}x${size}.svg`);
  fs.writeFileSync(svgPath, svgContent);

  console.log(`Created ${svgPath}`);
});

// Create a simple PNG fallback using canvas (Node.js)
// Note: This requires node-canvas which may not be installed
// For production, use proper image generation tools like sharp or ImageMagick

console.log('\nIcon generation complete!');
console.log('Note: SVG icons created. For production, convert to PNG using:');
console.log('  - sharp (npm package)');
console.log('  - ImageMagick');
console.log('  - Online tools like https://cloudconvert.com/');
