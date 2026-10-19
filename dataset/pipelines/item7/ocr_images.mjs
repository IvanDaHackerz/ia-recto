import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error(`Invalid argument near ${key ?? "<end>"}`);
    }
    args[key.slice(2)] = value;
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
for (const required of ["manifest", "output", "lang-path", "module-root"]) {
  if (!args[required]) throw new Error(`Missing --${required}`);
}

const manifest = JSON.parse(fs.readFileSync(args.manifest, "utf8"));
if (!Array.isArray(manifest) || manifest.length === 0) {
  throw new Error("OCR manifest must be a non-empty JSON array.");
}

const require = createRequire(path.join(args["module-root"], "package.json"));
const { createWorker, PSM } = require("tesseract.js");

const worker = await createWorker("eng", 1, {
  langPath: args["lang-path"],
  cachePath: args["lang-path"],
  cacheMethod: "readOnly",
  gzip: true,
  logger: (message) => {
    if (message.status === "recognizing text") {
      process.stderr.write(`\rOCR ${(message.progress * 100).toFixed(0)}%`);
    }
  },
});

await worker.setParameters({
  tessedit_pageseg_mode: PSM.AUTO,
  preserve_interword_spaces: "1",
  user_defined_dpi: "300",
});

const output = fs.createWriteStream(args.output, { encoding: "utf8" });
try {
  for (const item of manifest) {
    if (!item.image_path || !fs.existsSync(item.image_path)) {
      throw new Error(`OCR image not found: ${item.image_path}`);
    }
    const result = await worker.recognize(item.image_path, {}, { text: true, tsv: true });
    output.write(`${JSON.stringify({
      ...item,
      text: result.data.text ?? "",
      confidence: Number.isFinite(result.data.confidence) ? result.data.confidence / 100 : null,
      tsv: result.data.tsv ?? null,
    })}\n`);
    process.stderr.write(`\rCompleted ${item.document_id ?? "document"} page ${item.pdf_page ?? "?"}          \n`);
  }
} finally {
  output.end();
  await worker.terminate();
}
