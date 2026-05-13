const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { pipeline } = require('stream/promises');
const { PDFImage } = require('pdf-image');
const config = require('./config');

async function saveCameraReadyParts(request) {
  let saved = null;

  for await (const part of request.parts()) {
    if (part.type !== 'file') continue;

    if (part.fieldname !== 'cameraReadyPdf') {
      part.file.resume();
      continue;
    }

    const filename = `${Date.now()}-${crypto.randomBytes(8).toString('hex')}.pdf`;
    const target = path.join(config.cameraReadyDir, filename);
    await pipeline(part.file, fs.createWriteStream(target));
    saved = {
      filePath: target,
      publicPath: `/public/camera-ready/${filename}`
    };
  }

  if (!saved) throw new Error('Camera-ready PDF is required');
  return saved;
}

async function buildThumbnail(pdfPath) {
  const pdf = new PDFImage(pdfPath, {
    outputDirectory: config.thumbnailsDir,
    convertOptions: {
      '-thumbnail': '480x360',
      '-background': 'white',
      '-alpha': 'remove'
    }
  });

  const imagePath = await pdf.convertPage(0);
  return `/public/camera-ready/thumbs/${path.basename(imagePath)}`;
}

async function prepareCameraReady(request) {
  const saved = await saveCameraReadyParts(request);
  const record = {
    pdfPath: saved.publicPath,
    thumbnailPath: '',
    thumbnailError: '',
    generator: 'pdf-image',
    preparedAt: new Date()
  };

  try {
    record.thumbnailPath = await buildThumbnail(saved.filePath);
  } catch (error) {
    record.thumbnailError = error.message || 'thumbnail generation failed';
  }

  return record;
}

module.exports = {
  prepareCameraReady
};
