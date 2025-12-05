import sharp from "sharp";
import fs from "fs-extra";
import path from "path";

const inputFolder = "./public/images/inventions/africa/senegal";      // folder with your original images
const outputFolder = "./public/images/inventions/africa/senegal";// folder to save .webp files

async function convertImages() {
  await fs.ensureDir(outputFolder);

  const files = await fs.readdir(inputFolder);

  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    if (![".jpg", ".jpeg", ".png", ".gif", ".tiff", ".bmp", ".avif"].includes(ext)) {
      console.log(`Skipping unsupported file: ${file}`);
      continue;
    }

    const inputPath = path.join(inputFolder, file);
    const outputName = path.basename(file, ext) + ".webp";
    const outputPath = path.join(outputFolder, outputName);

    try {
      await sharp(inputPath)
        .webp({ quality: 100 })
        .toFile(outputPath);

      console.log(`Converted: ${file} → ${outputName}`);
    } catch (err) {
      console.error(`Error converting ${file}:`, err);
    }
  }

  console.log("Done!");
}

convertImages();
