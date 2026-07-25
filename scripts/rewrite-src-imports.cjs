const fs = require("fs");
const path = require("path");

const root = process.cwd();
const srcDir = path.join(root, "src");

function toPosix(p) {
  return p.split(path.sep).join("/");
}

function walk(dir, files) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, files);
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
}

function convertSpecifier(spec, currentFileRelPosix) {
  if (!spec.startsWith("src/")) {
    return spec;
  }

  const currentDir = path.posix.dirname(currentFileRelPosix);
  let relative = path.posix.relative(currentDir, spec);
  if (!relative.startsWith(".")) {
    relative = `./${relative}`;
  }
  return relative;
}

const files = [];
walk(srcDir, files);

let changedFiles = 0;

for (const file of files) {
  const fileRelPosix = toPosix(path.relative(root, file));
  const original = fs.readFileSync(file, "utf8");

  const updated = original
    .replace(/(from\s+["'])(src\/[\w\-./]+)(["'])/g, (_, prefix, spec, suffix) => {
      return `${prefix}${convertSpecifier(spec, fileRelPosix)}${suffix}`;
    })
    .replace(/(import\(\s*["'])(src\/[\w\-./]+)(["']\s*\))/g, (_, prefix, spec, suffix) => {
      return `${prefix}${convertSpecifier(spec, fileRelPosix)}${suffix}`;
    });

  if (updated !== original) {
    fs.writeFileSync(file, updated, "utf8");
    changedFiles += 1;
  }
}

console.log(`Rewrote imports in ${changedFiles} files.`);
