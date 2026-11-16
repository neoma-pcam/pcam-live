const fs = require('fs');
const path = require('path');

const srcSvg = path.join(__dirname, 'nodes', 'NeomaPcam', 'neomapcam.svg');
const dstDir = path.join(__dirname, 'dist', 'nodes', 'NeomaPcam');
fs.mkdirSync(dstDir, { recursive: true });
fs.copyFileSync(srcSvg, path.join(dstDir, 'neomapcam.svg'));