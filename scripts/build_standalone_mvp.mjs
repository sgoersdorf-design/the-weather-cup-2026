#!/usr/bin/env node

import { copyFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const mvpDir = resolve(root, "website/mvp");
const outputPath = resolve(mvpDir, "wm-2026-weather-fit-mvp.html");
const staticAssetNames = [
  "apple-touch-icon.png",
  "favicon-16.png",
  "favicon-32.png",
  "icon-192.png",
  "icon-512.png",
  "icon-1024.png",
  "og-image.png",
  "site.webmanifest",
];

function readMvpFile(name) {
  return readFileSync(resolve(mvpDir, name), "utf8");
}

function inlineScript(source) {
  return source.replaceAll("</script", "<\\/script");
}

let html = readMvpFile("index.html");
const css = readMvpFile("styles.css");
const data = readMvpFile("data.js");
const mapData = readMvpFile("map-data.js");
const app = readMvpFile("app.js");
const outputDir = resolve(outputPath, "..");

html = html
  .replace('<link rel="stylesheet" href="./styles.css">', `<style>\n${css}\n</style>`)
  .replace('<script src="./data.js"></script>', `<script>\n${inlineScript(data)}\n</script>`)
  .replace('<script src="./map-data.js"></script>', `<script>\n${inlineScript(mapData)}\n</script>`)
  .replace('<script src="./app.js"></script>', `<script>\n${inlineScript(app)}\n</script>`);

writeFileSync(outputPath, html, "utf8");
for (const name of staticAssetNames) {
  const sourcePath = resolve(mvpDir, name);
  const targetPath = resolve(outputDir, name);
  if (existsSync(sourcePath) && sourcePath !== targetPath) {
    copyFileSync(sourcePath, targetPath);
  }
}
console.log(outputPath);
